"""
DataVista+ NLQ & Query API
Natural Language Query processing, SQL playground, and query history
"""
import time
import sqlite3
import logging
import pandas as pd
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user_model import User
from app.models.query_model import Query, SavedQuery
from app.models.report_model import ActivityLog
from app.models.dataset_model import Dataset
from app.services.text_to_sql import TextToSQLEngine
from app.core.security import sanitize_sql_input
from app.core.config import settings

router = APIRouter(prefix="/queries", tags=["Queries & NLQ"])
logger = logging.getLogger(__name__)


class NLQRequest(BaseModel):
    query: str
    dataset_id: Optional[int] = None


class SQLExecuteRequest(BaseModel):
    sql: str
    dataset_id: Optional[int] = None


class SaveQueryRequest(BaseModel):
    query_id: int
    name: str
    description: Optional[str] = None
    is_favorite: bool = False
    tags: Optional[List[str]] = []


# ─── NLQ → SQL ────────────────────────────────────────────────────────────────

@router.post("/nlq")
async def natural_language_query(
    request: NLQRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Process a natural language query and return generated SQL + results."""
    if not request.query or len(request.query.strip()) < 3:
        raise HTTPException(status_code=400, detail="Query is too short")

    engine = TextToSQLEngine()
    start_time = time.time()

    # Generate SQL
    result = engine.convert(request.query)
    sql = result["sql"]

    # Execute against the demo SQLite database or dataset
    execution_time = int((time.time() - start_time) * 1000)
    data_rows = []
    columns = []
    error = None

    try:
        db_path = "./datavista.db"
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchmany(1000)  # limit to 1000 rows
        if rows:
            columns = list(rows[0].keys())
            data_rows = [dict(row) for row in rows]
        conn.close()
    except sqlite3.OperationalError as e:
        error = str(e)
        # Return mock data if table doesn't exist
        data_rows = _get_mock_data(result["intent"])
        columns = list(data_rows[0].keys()) if data_rows else []

    # Save query to history
    query_record = Query(
        user_id=current_user.id,
        dataset_id=request.dataset_id,
        natural_language_query=request.query,
        generated_sql=sql,
        sql_explanation=result["explanation"],
        intent=result["intent"],
        confidence_score=result["confidence"],
        execution_time_ms=execution_time,
        row_count_returned=len(data_rows),
        status="success" if not error else "error",
        error_message=error,
    )
    db.add(query_record)
    db.add(ActivityLog(user_id=current_user.id, action_type="query", description=f"NLQ: {request.query[:100]}"))
    await db.commit()
    await db.refresh(query_record)

    return {
        "query_id": query_record.id,
        "natural_query": request.query,
        "generated_sql": sql,
        "explanation": result["explanation"],
        "intent": result["intent"],
        "confidence": result["confidence"],
        "warnings": result.get("warnings", []),
        "nlp_analysis": result.get("nlp_result", {}),
        "results": {
            "columns": columns,
            "rows": data_rows,
            "row_count": len(data_rows),
            "execution_time_ms": execution_time,
        },
        "error": error,
    }


# ─── SQL Playground ────────────────────────────────────────────────────────────

@router.post("/execute")
async def execute_sql(
    request: SQLExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Execute raw SQL (SQL playground). Validates and prevents injection."""
    sql = sanitize_sql_input(request.sql.strip())

    start_time = time.time()
    data_rows = []
    columns = []

    try:
        conn = sqlite3.connect("./datavista.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchmany(500)
        if rows:
            columns = list(rows[0].keys())
            data_rows = [dict(row) for row in rows]
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SQL Error: {str(e)}")

    execution_time = int((time.time() - start_time) * 1000)
    db.add(ActivityLog(user_id=current_user.id, action_type="sql_execute", description=sql[:200]))
    await db.commit()

    return {
        "columns": columns,
        "rows": data_rows,
        "row_count": len(data_rows),
        "execution_time_ms": execution_time,
    }


# ─── Query History ─────────────────────────────────────────────────────────────

@router.get("/history")
async def get_query_history(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get recent query history for current user."""
    result = await db.execute(
        select(Query)
        .where(Query.user_id == current_user.id)
        .order_by(desc(Query.created_at))
        .limit(limit)
    )
    queries = result.scalars().all()
    return [
        {
            "id": q.id,
            "natural_language_query": q.natural_language_query,
            "generated_sql": q.generated_sql,
            "intent": q.intent,
            "confidence_score": q.confidence_score,
            "row_count_returned": q.row_count_returned,
            "status": q.status,
            "created_at": q.created_at,
        }
        for q in queries
    ]


@router.post("/save")
async def save_query(
    request: SaveQueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save a query to favorites."""
    saved = SavedQuery(
        user_id=current_user.id,
        query_id=request.query_id,
        name=request.name,
        description=request.description,
        is_favorite=request.is_favorite,
        tags=request.tags or [],
    )
    db.add(saved)
    await db.commit()
    return {"message": "Query saved successfully"}


@router.get("/saved")
async def get_saved_queries(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List saved/favorite queries."""
    result = await db.execute(
        select(SavedQuery, Query)
        .join(Query, SavedQuery.query_id == Query.id)
        .where(SavedQuery.user_id == current_user.id)
        .order_by(desc(SavedQuery.created_at))
    )
    rows = result.all()
    return [
        {
            "id": saved.id,
            "name": saved.name,
            "description": saved.description,
            "is_favorite": saved.is_favorite,
            "tags": saved.tags,
            "query": {
                "id": query.id,
                "natural_language_query": query.natural_language_query,
                "generated_sql": query.generated_sql,
            },
            "created_at": saved.created_at,
        }
        for saved, query in rows
    ]


@router.get("/suggestions")
async def get_query_suggestions(
    q: str = "",
    current_user: User = Depends(get_current_user),
):
    """Return smart query suggestions based on input."""
    sample_suggestions = [
        "Show total revenue by region",
        "List top 10 customers by order value",
        "What is the average order value this month?",
        "Count orders by status",
        "Show monthly sales trend for last year",
        "Which products have the highest sales?",
        "Find customers who ordered more than 5 times",
        "Compare revenue between north and south regions",
        "Show employee count by department",
        "What is the profit margin for each product category?",
    ]
    if q:
        filtered = [s for s in sample_suggestions if q.lower() in s.lower()]
        return filtered[:5] or sample_suggestions[:5]
    return sample_suggestions[:8]


def _get_mock_data(intent: str) -> list:
    """Return mock data when database tables don't exist yet."""
    mock_datasets = {
        "AGGREGATE_SUM": [
            {"region": "North", "total_revenue": 1250000},
            {"region": "South", "total_revenue": 980000},
            {"region": "East", "total_revenue": 1100000},
            {"region": "West", "total_revenue": 920000},
        ],
        "AGGREGATE_COUNT": [
            {"status": "Completed", "count": 7234},
            {"status": "Pending", "count": 1890},
            {"status": "Cancelled", "count": 876},
        ],
        "SELECT": [
            {"order_id": 1001, "customer_id": 501, "total_amount": 249.99, "region": "North", "status": "Completed"},
            {"order_id": 1002, "customer_id": 502, "total_amount": 89.50, "region": "South", "status": "Completed"},
            {"order_id": 1003, "customer_id": 503, "total_amount": 479.00, "region": "East", "status": "Pending"},
            {"order_id": 1004, "customer_id": 504, "total_amount": 129.99, "region": "West", "status": "Completed"},
            {"order_id": 1005, "customer_id": 505, "total_amount": 599.00, "region": "North", "status": "Completed"},
        ],
    }
    return mock_datasets.get(intent, mock_datasets["SELECT"])
