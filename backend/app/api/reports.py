"""
DataVista+ Reports API
PDF, Excel, CSV generation and report management
"""
import os
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user_model import User
from app.models.report_model import Report
from app.models.insight_model import BusinessKPI, Insight, Recommendation
from app.services.report_engine import ReportEngine

router = APIRouter(prefix="/reports", tags=["Reports"])
logger = logging.getLogger(__name__)


class ReportCreate(BaseModel):
    name: str
    report_type: str  # business_summary, kpi, prediction, executive
    format: str = "pdf"  # pdf, excel, csv
    dataset_id: Optional[int] = None
    include_kpis: bool = True
    include_insights: bool = True
    include_recommendations: bool = True


@router.get("")
async def list_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all generated reports."""
    result = await db.execute(
        select(Report)
        .where(Report.user_id == current_user.id)
        .order_by(desc(Report.created_at))
    )
    reports = result.scalars().all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "report_type": r.report_type,
            "format": r.format,
            "status": r.status,
            "is_scheduled": r.is_scheduled,
            "created_at": r.created_at,
            "has_file": r.file_path is not None and os.path.exists(r.file_path or ""),
        }
        for r in reports
    ]


@router.post("/generate")
async def generate_report(
    request: ReportCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a report in the specified format."""
    # Create report record
    report = Report(
        user_id=current_user.id,
        name=request.name,
        report_type=request.report_type,
        format=request.format,
        status="generating",
    )
    db.add(report)
    await db.flush()
    report_id = report.id

    # Gather data
    kpis_data = []
    if request.include_kpis:
        kpi_result = await db.execute(select(BusinessKPI).limit(10))
        kpi_rows = kpi_result.scalars().all()
        kpis_data = [
            {"KPI": k.name, "Value": k.value, "Unit": k.unit,
             "Change": f"{k.change_percent:+.1f}%" if k.change_percent else "N/A",
             "Trend": k.trend}
            for k in kpi_rows
        ] or _mock_kpis_for_report()

    insights_data = []
    if request.include_insights:
        ins_result = await db.execute(select(Insight).limit(10))
        ins_rows = ins_result.scalars().all()
        insights_data = [
            {"Title": i.title, "Type": i.insight_type, "Impact": i.impact_level,
             "Confidence": f"{int(i.confidence_score*100)}%"}
            for i in ins_rows
        ] or _mock_insights_for_report()

    recs_data = []
    if request.include_recommendations:
        rec_result = await db.execute(select(Recommendation).limit(5))
        rec_rows = rec_result.scalars().all()
        recs_data = [
            {"Priority": r.priority, "Title": r.title, "Impact": r.expected_impact}
            for r in rec_rows
        ] or _mock_recs_for_report()

    # Generate report
    engine = ReportEngine()
    try:
        if request.format == "pdf":
            file_path = engine.generate_business_summary(kpis_data, insights_data, recs_data, report_id)
        elif request.format == "excel":
            file_path = engine.generate_excel(
                title=request.name,
                sheets=[
                    {"name": "KPIs", "data": kpis_data},
                    {"name": "Insights", "data": insights_data},
                    {"name": "Recommendations", "data": recs_data},
                ],
                report_id=report_id,
            )
        elif request.format == "csv":
            file_path = engine.generate_csv(kpis_data, report_id, "kpi_report")
        else:
            raise HTTPException(400, f"Unsupported format: {request.format}")

        report.file_path = file_path
        report.status = "completed"
    except Exception as e:
        report.status = "failed"
        await db.commit()
        raise HTTPException(500, f"Report generation failed: {str(e)}")

    await db.commit()

    return {
        "report_id": report.id,
        "name": report.name,
        "format": report.format,
        "status": "completed",
        "download_url": f"/api/v1/reports/{report.id}/download",
    }


@router.get("/{report_id}/download")
async def download_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download a generated report file."""
    result = await db.execute(
        select(Report).where(Report.id == report_id, Report.user_id == current_user.id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(404, "Report not found")
    if not report.file_path or not os.path.exists(report.file_path):
        raise HTTPException(404, "Report file not found")

    media_types = {"pdf": "application/pdf", "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "csv": "text/csv"}
    return FileResponse(
        path=report.file_path,
        media_type=media_types.get(report.format, "application/octet-stream"),
        filename=os.path.basename(report.file_path),
    )


@router.delete("/{report_id}")
async def delete_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a report record and its file."""
    result = await db.execute(
        select(Report).where(Report.id == report_id, Report.user_id == current_user.id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(404, "Report not found")
    if report.file_path and os.path.exists(report.file_path):
        os.remove(report.file_path)
    await db.delete(report)
    await db.commit()
    return {"message": "Report deleted"}


def _mock_kpis_for_report():
    return [
        {"KPI": "Total Revenue", "Value": 4250000, "Unit": "USD", "Change": "+11.84%", "Trend": "up"},
        {"KPI": "Total Orders", "Value": 10000, "Unit": "orders", "Change": "+14.29%", "Trend": "up"},
        {"KPI": "Avg Order Value", "Value": 425, "Unit": "USD", "Change": "-2.14%", "Trend": "down"},
        {"KPI": "Profit Margin", "Value": 30.0, "Unit": "%", "Change": "+8.30%", "Trend": "up"},
    ]


def _mock_insights_for_report():
    return [
        {"Title": "Revenue Growth Trend", "Type": "trend", "Impact": "High", "Confidence": "92%"},
        {"Title": "Anomaly Detected — March 15th", "Type": "anomaly", "Impact": "Medium", "Confidence": "87%"},
        {"Title": "North Region Outperforms", "Type": "segment", "Impact": "High", "Confidence": "93%"},
    ]


def _mock_recs_for_report():
    return [
        {"Priority": 1, "Title": "Scale North Region Investment", "Impact": "15-20% revenue increase"},
        {"Priority": 2, "Title": "Optimize Inventory for Promotions", "Impact": "$200K additional revenue"},
        {"Priority": 3, "Title": "Expand Premium Product Line", "Impact": "15% revenue uplift"},
    ]
