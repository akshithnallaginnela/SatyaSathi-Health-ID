from datetime import date, datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from database import get_db, async_session
from models.domain import (
    BPReading, SugarReading, UserDataStatus,
    BPCreate, SugarCreate, User, CoinLedger
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
    """Log BP and trigger analysis. Awards 20 coins if last BP was 7+ days ago."""
    # Check previous BP reading date BEFORE adding the new one
    prev_result = await db.execute(
        select(BPReading)
        .where(BPReading.user_id == user_id)
        .order_by(desc(BPReading.measured_at))
        .limit(1)
    )
    prev_bp = prev_result.scalar_one_or_none()
    
    coins_awarded = 0
    streak_bonus = False
    if prev_bp:
        days_since = (datetime.utcnow() - prev_bp.measured_at).days
        if days_since >= 7:
            coins_awarded = 20
            streak_bonus = True

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

    if coins_awarded > 0:
        db.add(CoinLedger(
            user_id=user_id,
            amount=coins_awarded,
            activity_type="BP_WEEKLY_STREAK"
        ))

    await db.commit()

    # Trigger AI analysis in fresh session so it sees the new reading
    try:
        async with async_session() as analysis_db:
            analysis = await run_full_analysis(user_id, analysis_db)
            await analysis_db.commit()
        print(f"BP logged + analysis done, tasks={len(analysis.get('tasks',[])) if analysis else 0}")
    except Exception as e:
        print(f"Analysis error after BP log: {e}")
        analysis = None

    return {
        "message": "BP logged and analysis updated",
        "reading": {
            "systolic": new_reading.systolic,
            "diastolic": new_reading.diastolic,
            "date": str(new_reading.date)
        },
        "coins_awarded": coins_awarded,
        "streak_bonus": streak_bonus,
        "analysis_updated": analysis is not None
    }

@router.post("/sugar")
async def log_sugar(
    reading: SugarCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Log Sugar and trigger analysis. Awards 20 coins if last sugar was 7+ days ago."""
    # Check previous sugar reading date BEFORE adding the new one
    prev_result = await db.execute(
        select(SugarReading)
        .where(SugarReading.user_id == user_id)
        .order_by(desc(SugarReading.measured_at))
        .limit(1)
    )
    prev_sugar = prev_result.scalar_one_or_none()

    coins_awarded = 0
    streak_bonus = False
    if prev_sugar:
        days_since = (datetime.utcnow() - prev_sugar.measured_at).days
        if days_since >= 7:
            coins_awarded = 20
            streak_bonus = True

    new_reading = SugarReading(
        user_id=user_id,
        fasting_glucose=reading.fasting_glucose,
        date=date.today()
    )
    db.add(new_reading)
    await _update_status(user_id, "sugar", db)

    if coins_awarded > 0:
        db.add(CoinLedger(
            user_id=user_id,
            amount=coins_awarded,
            activity_type="SUGAR_WEEKLY_STREAK"
        ))

    await db.commit()

    # Trigger AI analysis in fresh session so it sees the new reading
    try:
        async with async_session() as analysis_db:
            analysis = await run_full_analysis(user_id, analysis_db)
            await analysis_db.commit()
        print(f"Sugar logged + analysis done, tasks={len(analysis.get('tasks',[])) if analysis else 0}")
    except Exception as e:
        print(f"Analysis error after Sugar log: {e}")
        analysis = None

    return {
        "message": "Sugar logged and analysis updated",
        "reading": {
            "fasting_glucose": new_reading.fasting_glucose,
            "date": str(new_reading.date)
        },
        "coins_awarded": coins_awarded,
        "streak_bonus": streak_bonus,
        "analysis_updated": analysis is not None
    }

@router.get("/history")
async def get_vitals_history(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get history of BP and Sugar readings."""
    bp_rows = await db.execute(
        select(BPReading).where(BPReading.user_id == user_id).order_by(desc(BPReading.measured_at)).limit(10)
    )
    sugar_rows = await db.execute(
        select(SugarReading).where(SugarReading.user_id == user_id).order_by(desc(SugarReading.measured_at)).limit(10)
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
    
    await db.commit()

    # Trigger AI analysis in fresh session so it sees updated BMI
    try:
        async with async_session() as analysis_db:
            await run_full_analysis(user_id, analysis_db)
            await analysis_db.commit()
    except Exception as e:
        print(f"⚠️ Analysis error after BMI log: {e}")
    
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
