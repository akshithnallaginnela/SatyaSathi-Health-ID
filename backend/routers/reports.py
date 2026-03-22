"""
Reports router — list and retrieve analyzed health reports.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from database import get_db
from security.jwt_handler import get_current_user_id
from models.report import Report, ReportResponse

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/", response_model=list[ReportResponse])
async def list_reports(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List report history for current user."""
    offset = (page - 1) * limit
    result = await db.execute(
        select(Report)
        .where(Report.user_id == user_id)
        .order_by(desc(Report.uploaded_at))
        .offset(offset)
        .limit(limit)
    )
    reports = result.scalars().all()
    return [ReportResponse.model_validate(r) for r in reports]


@router.get("/{report_id}")
async def get_report_detail(
    report_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get full report details including extracted OCR + ML payload."""
    result = await db.execute(
        select(Report).where(Report.id == report_id, Report.user_id == user_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    return {
        "id": report.id,
        "report_type": report.report_type,
        "file_key": report.file_key,
        "extracted_values": report.extracted_values,
        "upload_status": report.upload_status,
        "ocr_confidence": float(report.ocr_confidence) if report.ocr_confidence is not None else None,
        "uploaded_at": report.uploaded_at,
        "report_date": report.report_date,
    }
