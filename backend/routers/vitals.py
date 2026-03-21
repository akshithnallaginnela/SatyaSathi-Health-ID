"""
Vitals router — log BP, glucose, BMI, and retrieve vitals history.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from database import get_db
from models.health_record import (
    VitalsLog, BodyMetrics,
    BPReading, GlucoseReading, BMIEntry,
    VitalsResponse, BodyMetricsResponse,
)
from security.jwt_handler import get_current_user_id

router = APIRouter(prefix="/api/vitals", tags=["Vitals"])


@router.post("/bp", response_model=VitalsResponse)
async def log_bp(
    reading: BPReading,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Log a blood pressure reading."""
    vitals = VitalsLog(
        user_id=user_id,
        systolic=reading.systolic,
        diastolic=reading.diastolic,
        pulse=reading.pulse,
        measured_at=reading.measured_at or datetime.utcnow(),
    )
    db.add(vitals)
    await db.flush()
    return VitalsResponse.model_validate(vitals)


@router.post("/glucose", response_model=VitalsResponse)
async def log_glucose(
    reading: GlucoseReading,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Log a fasting glucose reading."""
    vitals = VitalsLog(
        user_id=user_id,
        fasting_glucose=reading.fasting_glucose,
        measured_at=reading.measured_at or datetime.utcnow(),
    )
    db.add(vitals)
    await db.flush()
    return VitalsResponse.model_validate(vitals)


@router.post("/bmi", response_model=BodyMetricsResponse)
async def log_bmi(
    entry: BMIEntry,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Log body metrics (weight, height → auto-calculates BMI)."""
    bmi_value = round(entry.weight_kg / ((entry.height_cm / 100) ** 2), 1)
    metrics = BodyMetrics(
        user_id=user_id,
        weight_kg=entry.weight_kg,
        height_cm=entry.height_cm,
        bmi=bmi_value,
        waist_cm=entry.waist_cm,
    )
    db.add(metrics)
    await db.flush()
    return BodyMetricsResponse.model_validate(metrics)


@router.get("/history")
async def get_vitals_history(
    limit: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get recent vitals readings for the current user."""
    result = await db.execute(
        select(VitalsLog)
        .where(VitalsLog.user_id == user_id)
        .order_by(desc(VitalsLog.measured_at))
        .limit(limit)
    )
    vitals = result.scalars().all()
    return [VitalsResponse.model_validate(v) for v in vitals]


@router.get("/bmi/latest", response_model=Optional[BodyMetricsResponse])
async def get_latest_bmi(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get the latest body metrics entry."""
    result = await db.execute(
        select(BodyMetrics)
        .where(BodyMetrics.user_id == user_id)
        .order_by(desc(BodyMetrics.measured_at))
        .limit(1)
    )
    metrics = result.scalar_one_or_none()
    if not metrics:
        return None
    return BodyMetricsResponse.model_validate(metrics)
