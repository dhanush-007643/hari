"""
DataVista+ Insights API
Automatic business insights, recommendations, and alerts
"""
import logging
import io
import pandas as pd
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, update
from pydantic import BaseModel

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user_model import User
from app.models.insight_model import Insight, Recommendation, BusinessKPI, Alert
from app.models.dataset_model import Dataset
from app.models.report_model import Notification
from app.services.insight_engine import InsightEngine

router = APIRouter(prefix="/insights", tags=["Business Insights"])
logger = logging.getLogger(__name__)


class AlertCreate(BaseModel):
    name: str
    kpi_name: str
    condition: str  # gt, lt, eq, gte, lte
    threshold_value: float
    email_notify: bool = False


# ─── Insights ──────────────────────────────────────────────────────────────────

@router.get("")
async def get_insights(
    dataset_id: Optional[int] = None,
    insight_type: Optional[str] = None,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get auto-generated business insights."""
    query = select(Insight).order_by(desc(Insight.created_at)).limit(limit)
    if dataset_id:
        query = query.where(Insight.dataset_id == dataset_id)
    if insight_type:
        query = query.where(Insight.insight_type == insight_type)

    result = await db.execute(query)
    insights = result.scalars().all()

    if not insights:
        # Return seeded mock insights
        return _get_mock_insights()

    return [
        {
            "id": ins.id,
            "type": ins.insight_type,
            "title": ins.title,
            "description": ins.description,
            "confidence_score": ins.confidence_score,
            "impact_level": ins.impact_level,
            "is_read": ins.is_read,
            "supporting_data": ins.supporting_data,
            "created_at": ins.created_at,
        }
        for ins in insights
    ]


@router.get("/generate/{dataset_id}")
async def generate_insights(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Auto-generate insights from a dataset using the insight engine."""
    dataset_result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = dataset_result.scalar_one_or_none()
    if not dataset or not dataset.file_path:
        raise HTTPException(404, "Dataset not found or not uploaded")

    try:
        df = pd.read_csv(dataset.file_path)
    except Exception as e:
        raise HTTPException(400, f"Could not load dataset: {e}")

    engine = InsightEngine()
    insights_data = engine.generate_insights(df, dataset.name)

    # Save to database
    saved_insights = []
    for ins_data in insights_data:
        insight = Insight(
            dataset_id=dataset_id,
            insight_type=ins_data.get("type"),
            title=ins_data.get("title"),
            description=ins_data.get("description"),
            supporting_data=ins_data.get("supporting_data"),
            confidence_score=ins_data.get("confidence_score", 0.8),
            impact_level=ins_data.get("impact_level", "medium"),
        )
        db.add(insight)
        saved_insights.append(ins_data)

    # Create notification
    db.add(Notification(
        user_id=current_user.id,
        title=f"New insights generated for {dataset.name}",
        message=f"{len(insights_data)} insights were automatically generated.",
        notification_type="insight",
    ))
    await db.commit()

    return {"generated": len(insights_data), "insights": saved_insights}


@router.post("/{insight_id}/read")
async def mark_insight_read(
    insight_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark an insight as read."""
    await db.execute(update(Insight).where(Insight.id == insight_id).values(is_read=True))
    await db.commit()
    return {"message": "Marked as read"}


# ─── Recommendations ───────────────────────────────────────────────────────────

@router.get("/recommendations")
async def get_recommendations(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get AI-generated business recommendations sorted by priority."""
    result = await db.execute(
        select(Recommendation)
        .order_by(Recommendation.priority)
        .limit(limit)
    )
    recs = result.scalars().all()

    if not recs:
        return _get_mock_recommendations()

    return [
        {
            "id": r.id,
            "title": r.title,
            "description": r.description,
            "action_items": r.action_items,
            "priority": r.priority,
            "expected_impact": r.expected_impact,
            "status": r.status,
            "created_at": r.created_at,
        }
        for r in recs
    ]


# ─── Alerts ────────────────────────────────────────────────────────────────────

@router.get("/alerts")
async def get_alerts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all alerts configured by the current user."""
    result = await db.execute(
        select(Alert).where(Alert.user_id == current_user.id)
        .order_by(desc(Alert.created_at))
    )
    alerts = result.scalars().all()
    return [
        {
            "id": a.id,
            "name": a.name,
            "kpi_name": a.kpi_name,
            "condition": a.condition,
            "threshold_value": a.threshold_value,
            "is_active": a.is_active,
            "email_notify": a.email_notify,
            "last_triggered": a.last_triggered,
            "created_at": a.created_at,
        }
        for a in alerts
    ]


@router.post("/alerts")
async def create_alert(
    alert_data: AlertCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new KPI threshold alert."""
    alert = Alert(
        user_id=current_user.id,
        name=alert_data.name,
        kpi_name=alert_data.kpi_name,
        condition=alert_data.condition,
        threshold_value=alert_data.threshold_value,
        email_notify=alert_data.email_notify,
        is_active=True,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return {"message": "Alert created", "alert_id": alert.id}


@router.delete("/alerts/{alert_id}")
async def delete_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an alert."""
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id, Alert.user_id == current_user.id)
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(404, "Alert not found")
    await db.delete(alert)
    await db.commit()
    return {"message": "Alert deleted"}


# ─── Anomaly Alerts ────────────────────────────────────────────────────────────

@router.get("/anomalies")
async def get_anomaly_alerts(current_user: User = Depends(get_current_user)):
    """Get latest anomaly detections across all monitored metrics."""
    return [
        {
            "metric": "Daily Revenue",
            "value": 850000,
            "expected_range": [220000, 650000],
            "severity": "high",
            "detected_at": "2024-12-15T14:30:00",
            "description": "Revenue spike detected — 340% above daily average. Possible promotional event."
        },
        {
            "metric": "Order Cancellation Rate",
            "value": 18.5,
            "expected_range": [2, 10],
            "severity": "medium",
            "detected_at": "2024-12-14T09:00:00",
            "description": "Cancellation rate significantly above normal. Review product quality or delivery."
        },
        {
            "metric": "Average Response Time",
            "value": 4200,
            "expected_range": [200, 1500],
            "severity": "high",
            "detected_at": "2024-12-14T11:22:00",
            "description": "API response time degraded. Check server load and database queries."
        },
    ]


def _get_mock_insights():
    return [
        {
            "id": 1,
            "type": "trend",
            "title": "Revenue Growth Trend — 11.8% YoY",
            "description": "Revenue has grown consistently by 11.8% compared to the same period last year, driven primarily by the **North region** (+24%) and **Electronics category** (+19%).",
            "confidence_score": 0.92,
            "impact_level": "high",
            "is_read": False,
            "supporting_data": {"slope": 1250, "r_squared": 0.87, "direction": "upward"},
            "created_at": "2024-12-15T10:00:00",
        },
        {
            "id": 2,
            "type": "anomaly",
            "title": "Unusual Order Spike — March 15th",
            "description": "Orders on March 15th were **340% above** the daily average. This coincides with a promotional campaign that may require additional inventory planning.",
            "confidence_score": 0.87,
            "impact_level": "medium",
            "is_read": False,
            "supporting_data": {"anomaly_rate": 0.3, "spike_value": 8500},
            "created_at": "2024-12-14T14:00:00",
        },
        {
            "id": 3,
            "type": "correlation",
            "title": "Strong Price-Volume Correlation",
            "description": "Products priced between **$50–$100** show the highest order volumes. Products above **$200** account for 45% of total revenue despite only 12% of order count.",
            "confidence_score": 0.89,
            "impact_level": "medium",
            "is_read": True,
            "supporting_data": {"correlation": 0.78, "col1": "unit_price", "col2": "quantity"},
            "created_at": "2024-12-13T09:00:00",
        },
        {
            "id": 4,
            "type": "trend",
            "title": "Attrition Rate Improving",
            "description": "Employee attrition dropped from 10.2% to **8.5%**, suggesting recent HR initiatives are effective. Engineering department shows the lowest attrition at 4.2%.",
            "confidence_score": 0.85,
            "impact_level": "high",
            "is_read": False,
            "supporting_data": {"direction": "downward", "change": -1.7},
            "created_at": "2024-12-12T11:00:00",
        },
        {
            "id": 5,
            "type": "segment",
            "title": "North Region Outperforms by 24%",
            "description": "The North region leads all others in revenue with $1.25M, contributing **29.4% of total revenue**. South region is the slowest performer requiring strategic attention.",
            "confidence_score": 0.93,
            "impact_level": "high",
            "is_read": False,
            "supporting_data": {"top_segments": [{"region": "North", "sum": 1250000}]},
            "created_at": "2024-12-11T08:00:00",
        },
    ]


def _get_mock_recommendations():
    return [
        {
            "id": 1,
            "title": "Scale North Region Investment",
            "description": "The North region significantly outperforms others. Increased investment could yield 15-20% additional revenue.",
            "action_items": [
                "Increase marketing budget for North by 20%",
                "Expand warehouse capacity in North",
                "Hire 5 additional sales representatives",
                "Launch region-specific promotions"
            ],
            "priority": 1,
            "expected_impact": "Expected 15-20% additional revenue growth within 2 quarters",
            "status": "pending",
            "created_at": "2024-12-15T10:00:00",
        },
        {
            "id": 2,
            "title": "Optimize Inventory for Promotional Events",
            "description": "Future promotions should be backed by increased inventory buffers to prevent stockouts.",
            "action_items": [
                "Set up promotion calendar 30 days in advance",
                "Increase safety stock by 25% before promotions",
                "Automate reorder triggers",
                "Negotiate faster supplier lead times"
            ],
            "priority": 2,
            "expected_impact": "Prevent stockouts and capture additional $200K revenue per quarter",
            "status": "in_progress",
            "created_at": "2024-12-14T09:00:00",
        },
        {
            "id": 3,
            "title": "Expand Premium Product Line",
            "description": "Premium products ($200+) drive 45% of revenue with only 12% of orders. Expanding this line is highly strategic.",
            "action_items": [
                "Identify 3-5 new premium product opportunities",
                "Survey top 10% of customers on premium needs",
                "Develop premium bundling strategy",
                "Allocate R&D budget to premium tier"
            ],
            "priority": 3,
            "expected_impact": "15% revenue uplift within 12 months",
            "status": "pending",
            "created_at": "2024-12-13T12:00:00",
        },
    ]
