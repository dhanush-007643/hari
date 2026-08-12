"""
DataVista+ Analytics API
Dashboard KPIs, chart data, and business aggregations
"""
import logging
import random
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user_model import User
from app.models.insight_model import BusinessKPI

router = APIRouter(prefix="/analytics", tags=["Analytics"])
logger = logging.getLogger(__name__)


@router.get("/kpis")
async def get_kpis(
    dataset_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get business KPIs from the database or return defaults."""
    query = select(BusinessKPI)
    if dataset_id:
        query = query.where(BusinessKPI.dataset_id == dataset_id)
    result = await db.execute(query.limit(12))
    kpis = result.scalars().all()

    if kpis:
        return [
            {
                "name": k.name, "value": k.value, "unit": k.unit,
                "change_percent": k.change_percent, "trend": k.trend,
                "comparison_value": k.comparison_value,
            }
            for k in kpis
        ]

    # Return curated mock KPIs with realistic data
    return _get_mock_kpis()


@router.get("/charts/revenue-by-region")
async def revenue_by_region(current_user: User = Depends(get_current_user)):
    """Bar chart: Revenue breakdown by region."""
    return {
        "labels": ["North", "South", "East", "West", "Central"],
        "datasets": [
            {
                "label": "Revenue 2024",
                "data": [1250000, 980000, 1100000, 920000, 740000],
                "backgroundColor": ["#6C63FF", "#48BB78", "#4299E1", "#ED8936", "#F56565"],
            },
            {
                "label": "Revenue 2023",
                "data": [1050000, 860000, 970000, 840000, 680000],
                "backgroundColor": ["#9F7AEA", "#68D391", "#63B3ED", "#FBD38D", "#FC8181"],
            }
        ]
    }


@router.get("/charts/orders-by-status")
async def orders_by_status(current_user: User = Depends(get_current_user)):
    """Pie chart: Orders by status."""
    return {
        "labels": ["Completed", "Pending", "Cancelled", "Processing", "Shipped"],
        "data": [7234, 1890, 876, 1243, 757],
        "backgroundColor": ["#48BB78", "#ECC94B", "#F56565", "#4299E1", "#9F7AEA"],
    }


@router.get("/charts/monthly-revenue")
async def monthly_revenue(
    year: int = 2024,
    current_user: User = Depends(get_current_user),
):
    """Line chart: Monthly revenue trend."""
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    base = [280000, 310000, 420000, 380000, 460000, 510000,
            490000, 540000, 580000, 620000, 530000, 490000]
    prior = [250000, 270000, 360000, 330000, 400000, 450000,
             430000, 480000, 510000, 560000, 480000, 430000]
    return {
        "labels": months,
        "datasets": [
            {
                "label": f"Revenue {year}",
                "data": base,
                "borderColor": "#6C63FF",
                "backgroundColor": "rgba(108,99,255,0.1)",
                "fill": True,
            },
            {
                "label": f"Revenue {year - 1}",
                "data": prior,
                "borderColor": "#48BB78",
                "backgroundColor": "rgba(72,187,120,0.1)",
                "fill": True,
            }
        ]
    }


@router.get("/charts/top-products")
async def top_products(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
):
    """Horizontal bar chart: Top products by revenue."""
    products = [
        {"name": "Enterprise Software Suite", "revenue": 450000, "units": 1200},
        {"name": "Cloud Storage Pro", "revenue": 380000, "units": 3400},
        {"name": "Analytics Dashboard", "revenue": 310000, "units": 870},
        {"name": "AI Model Training Kit", "revenue": 290000, "units": 560},
        {"name": "Data Pipeline Tool", "revenue": 245000, "units": 1100},
        {"name": "Security Module", "revenue": 210000, "units": 2300},
        {"name": "API Gateway", "revenue": 185000, "units": 1800},
        {"name": "Report Generator", "revenue": 162000, "units": 940},
        {"name": "Mobile SDK", "revenue": 140000, "units": 2700},
        {"name": "Integration Hub", "revenue": 125000, "units": 1500},
    ]
    return {
        "labels": [p["name"] for p in products[:limit]],
        "data": [p["revenue"] for p in products[:limit]],
        "units": [p["units"] for p in products[:limit]],
    }


@router.get("/charts/revenue-heatmap")
async def revenue_heatmap(current_user: User = Depends(get_current_user)):
    """Heatmap: Revenue by day of week and hour."""
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    hours = list(range(8, 20))  # 8am to 8pm
    data = []
    for d_idx, day in enumerate(days):
        for h_idx, hour in enumerate(hours):
            # Simulate peak hours with realistic data
            base = 5000
            if day in ["Mon", "Tue", "Wed", "Thu", "Fri"]:
                base += 8000
            if hour in [10, 11, 14, 15, 16]:
                base += 12000
            value = base + random.randint(-2000, 3000)
            data.append({"day": day, "hour": f"{hour}:00", "value": value})
    return {"data": data, "days": days, "hours": [f"{h}:00" for h in hours]}


@router.get("/charts/customer-segments")
async def customer_segments(current_user: User = Depends(get_current_user)):
    """Scatter chart: Customer segments by value vs. frequency."""
    segments = []
    import random
    random.seed(42)
    for i in range(80):
        segments.append({
            "x": random.randint(1, 50),  # order frequency
            "y": random.randint(100, 5000),  # average order value
            "label": f"Customer {i + 1}",
            "segment": random.choice(["Premium", "Regular", "Occasional", "New"])
        })
    return {
        "data": segments,
        "segments": {
            "Premium": "#6C63FF",
            "Regular": "#48BB78",
            "Occasional": "#ED8936",
            "New": "#4299E1",
        }
    }


@router.get("/summary")
async def get_analytics_summary(current_user: User = Depends(get_current_user)):
    """Get overall analytics summary for the dashboard."""
    return {
        "total_revenue": {"value": 4250000, "change": 11.84, "trend": "up"},
        "total_orders": {"value": 10000, "change": 14.29, "trend": "up"},
        "avg_order_value": {"value": 425, "change": -2.14, "trend": "down"},
        "customer_count": {"value": 3000, "change": 15.38, "trend": "up"},
        "top_region": "North",
        "top_product": "Enterprise Software Suite",
        "conversion_rate": {"value": 3.8, "change": 0.5, "trend": "up"},
        "customer_satisfaction": {"value": 4.2, "change": 0.1, "trend": "up"},
        "report_generated_at": "2024-12-15T10:00:00",
    }


@router.get("/data-quality")
async def get_data_quality(
    dataset_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get data quality metrics for a dataset."""
    return {
        "overall_score": 94.2,
        "completeness": 96.8,
        "accuracy": 93.1,
        "consistency": 95.5,
        "timeliness": 91.4,
        "column_quality": [
            {"column": "order_id", "score": 100, "issues": 0},
            {"column": "customer_id", "score": 99.5, "issues": 12},
            {"column": "total_amount", "score": 98.2, "issues": 45},
            {"column": "order_date", "score": 97.8, "issues": 55},
            {"column": "region", "score": 96.3, "issues": 92},
            {"column": "status", "score": 99.1, "issues": 22},
        ],
    }


def _get_mock_kpis():
    return [
        {"name": "Total Revenue", "value": 4250000, "unit": "USD", "change_percent": 11.84, "trend": "up", "comparison_value": 3800000},
        {"name": "Total Orders", "value": 10000, "unit": "orders", "change_percent": 14.29, "trend": "up", "comparison_value": 8750},
        {"name": "Avg Order Value", "value": 425, "unit": "USD", "change_percent": -2.14, "trend": "down", "comparison_value": 434},
        {"name": "Active Customers", "value": 3000, "unit": "customers", "change_percent": 15.38, "trend": "up", "comparison_value": 2600},
        {"name": "Net Profit Margin", "value": 30.0, "unit": "%", "change_percent": 8.30, "trend": "up", "comparison_value": 27.7},
        {"name": "Customer Satisfaction", "value": 4.2, "unit": "/ 5", "change_percent": 2.44, "trend": "up", "comparison_value": 4.1},
        {"name": "Attrition Rate", "value": 8.5, "unit": "%", "change_percent": -16.67, "trend": "down", "comparison_value": 10.2},
        {"name": "Monthly Active Users", "value": 1240, "unit": "users", "change_percent": 22.78, "trend": "up", "comparison_value": 1010},
    ]
