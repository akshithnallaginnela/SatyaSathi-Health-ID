from datetime import date, datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from database import get_db
from models.domain import (
    BPReading, SugarReading, UserDataStatus, 
    BPCreate, SugarCreate, User
)
from security.jwt_handler import get_current_user_id
from ml.analysis_engine import run_full_analysis

router = APIRouter(prefix="/api/vitals", tags=["Vitals"])

async def _update_status(user_id: str, metric: str, db: AsyncSession):
    result = await db.execute(select(UserDataStatus).where(UserDataStatus.user_id == user_id))
    status = result.scalar_one_or_none()
    if not status:
        status = UserDataStatus(user_id=user_id)
        db.add(status)
    
    if metric == "bp":
        status.has_bp = True
        status.bp_count += 1
    elif metric == "sugar":
        status.has_sugar = True
        status.sugar_count += 1
    
    await db.flush()

@router.post("/bp")
async def log_bp(
    reading: BPCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Log BP and trigger analysis."""
    new_reading = BPReading(
        user_id=user_id,
        systolic=reading.systolic,
        diastolic=reading.diastolic,
        pulse=reading.pulse,
        time_of_day=reading.time_of_day,
        date=date.today()
    )
    db.add(new_reading)
    await _update_status(user_id, "bp", db)
    
    # Trigger AI analysis
    analysis = await run_full_analysis(user_id, db)
    await db.commit()
    
    return {
        "message": "BP logged and analysis updated",
        "reading": {
            "systolic": new_reading.systolic,
            "diastolic": new_reading.diastolic,
            "date": str(new_reading.date)
        },
        "analysis_summary": analysis
    }

@router.post("/sugar")
async def log_sugar(
    reading: SugarCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Log Sugar and trigger analysis."""
    new_reading = SugarReading(
        user_id=user_id,
        fasting_glucose=reading.fasting_glucose,
        date=date.today()
    )
    db.add(new_reading)
    await _update_status(user_id, "sugar", db)
    
    # Trigger AI analysis
    analysis = await run_full_analysis(user_id, db)
    await db.commit()
    
    return {
        "message": "Sugar logged and analysis updated",
        "reading": {
            "fasting_glucose": new_reading.fasting_glucose,
            "date": str(new_reading.date)
        },
        "analysis_summary": analysis
    }

@router.get("/history")
async def get_vitals_history(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get history of BP and Sugar readings."""
    bp_rows = await db.execute(
        select(BPReading).where(BPReading.user_id == user_id).order_by(desc(BPReading.date)).limit(10)
    )
    sugar_rows = await db.execute(
        select(SugarReading).where(SugarReading.user_id == user_id).order_by(desc(SugarReading.date)).limit(10)
    )
    
    bp_list = bp_rows.scalars().all()
    sugar_list = sugar_rows.scalars().all()
    
    return {
        "bp_history": [
            {
                "systolic": r.systolic,
                "diastolic": r.diastolic,
                "pulse": r.pulse,
                "time_of_day": r.time_of_day,
                "date": str(r.date),
                "measured_at": str(r.measured_at) if r.measured_at else None
            }
            for r in bp_list
        ],
        "sugar_history": [
            {
                "fasting_glucose": r.fasting_glucose,
                "date": str(r.date),
                "measured_at": str(r.measured_at) if r.measured_at else None
            }
            for r in sugar_list
        ]
    }

@router.post("/bmi")
async def log_bmi(
    data: dict,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update BMI and trigger analysis."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.weight_kg = data.get("weight_kg")
    user.height_cm = data.get("height_cm")
    user.waist_cm = data.get("waist_cm")
    
    if user.weight_kg and user.height_cm:
        user.bmi = round(user.weight_kg / ((user.height_cm / 100) ** 2), 2)
    
    # Trigger AI analysis
    await run_full_analysis(user_id, db)
    await db.commit()
    
    return {
        "message": "BMI updated",
        "bmi": user.bmi,
        "weight_kg": user.weight_kg,
        "height_cm": user.height_cm
    }

@router.get("/bmi/latest")
async def get_latest_bmi(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get most recent BMI/metrics."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return {
        "bmi": user.bmi or 0,
        "weight_kg": user.weight_kg or 0,
        "height_cm": user.height_cm or 0,
        "waist_cm": user.waist_cm or 0
    }
