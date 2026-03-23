"""
Diet Plan Router — Get personalized diet recommendations based on latest report.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from database import get_db
from security.jwt_handler import get_current_user_id
from models.report import Report

router = APIRouter(prefix="/api/diet", tags=["Diet Plan"])


@router.get("/plan")
async def get_diet_plan(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get personalized diet plan based on latest health report analysis."""
    
    # Get latest processed report
    result = await db.execute(
        select(Report)
        .where(Report.user_id == user_id, Report.upload_status == "processed")
        .order_by(desc(Report.uploaded_at))
        .limit(1)
    )
    latest_report = result.scalar_one_or_none()
    
    if not latest_report:
        return {
            "message": "No health reports found. Upload a report to get personalized diet recommendations.",
            "has_plan": False,
            "diet_plan": None,
        }
    
    if not isinstance(latest_report.extracted_values, dict):
        raise HTTPException(status_code=500, detail="Invalid report data format.")
    
    diet_plan = (latest_report.extracted_values or {}).get("diet_plan")
    ml_analysis = (latest_report.extracted_values or {}).get("ml_analysis") or {}
    
    if not diet_plan:
        return {
            "message": "Diet plan not available for this report. Please re-upload or contact support.",
            "has_plan": False,
            "diet_plan": None,
        }
    
    return {
        "message": "Diet plan generated successfully based on your latest report.",
        "has_plan": True,
        "diet_plan": diet_plan,
        "report_id": latest_report.id,
        "report_type": latest_report.report_type,
        "report_date": latest_report.uploaded_at,
        "risk_level": ml_analysis.get("risk_level", "low"),
    }


@router.get("/plan/{report_id}")
async def get_diet_plan_by_report(
    report_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get diet plan for a specific report."""
    
    result = await db.execute(
        select(Report).where(Report.id == report_id, Report.user_id == user_id)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    
    if not isinstance(report.extracted_values, dict):
        raise HTTPException(status_code=500, detail="Invalid report data format.")
    
    diet_plan = (report.extracted_values or {}).get("diet_plan")
    ml_analysis = (report.extracted_values or {}).get("ml_analysis") or {}
    
    if not diet_plan:
        raise HTTPException(
            status_code=404,
            detail="Diet plan not available for this report.",
        )
    
    return {
        "diet_plan": diet_plan,
        "report_id": report.id,
        "report_type": report.report_type,
        "report_date": report.uploaded_at,
        "risk_level": ml_analysis.get("risk_level", "low"),
    }
