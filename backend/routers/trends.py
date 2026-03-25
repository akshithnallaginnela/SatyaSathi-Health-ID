"""
Health Trends API — Historical data for charts
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from database import get_db
from models.domain import BPReading, SugarReading, User
from security.jwt_handler import get_current_user_id

router = APIRouter(prefix="/api/trends", tags=["Trends"])


@router.get("/bp")
async def get_bp_trend(
    days: int = Query(30, ge=7, le=365),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get BP readings for last N days"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(BPReading)
        .where(BPReading.user_id == user_id)
        .where(BPReading.measured_at >= cutoff_date)
        .order_by(BPReading.measured_at)
    )
    readings = result.scalars().all()
    
    # Format for charts
    data_points = []
    for r in readings:
        data_points.append({
            "date": r.measured_at.strftime("%Y-%m-%d"),
            "timestamp": r.measured_at.isoformat(),
            "systolic": r.systolic,
            "diastolic": r.diastolic,
            "pulse": r.pulse
        })
    
    # Calculate stats
    if readings:
        systolic_vals = [r.systolic for r in readings if r.systolic]
        diastolic_vals = [r.diastolic for r in readings if r.diastolic]
        
        stats = {
            "avg_systolic": round(sum(systolic_vals) / len(systolic_vals), 1) if systolic_vals else None,
            "avg_diastolic": round(sum(diastolic_vals) / len(diastolic_vals), 1) if diastolic_vals else None,
            "min_systolic": min(systolic_vals) if systolic_vals else None,
            "max_systolic": max(systolic_vals) if systolic_vals else None,
            "readings_count": len(readings),
            "trend": "improving" if len(systolic_vals) >= 2 and systolic_vals[-1] < systolic_vals[0] else "stable"
        }
    else:
        stats = {
            "avg_systolic": None,
            "avg_diastolic": None,
            "min_systolic": None,
            "max_systolic": None,
            "readings_count": 0,
            "trend": "no_data"
        }
    
    return {
        "data": data_points,
        "stats": stats,
        "period_days": days
    }


@router.get("/sugar")
async def get_sugar_trend(
    days: int = Query(30, ge=7, le=365),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get sugar readings for last N days"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(SugarReading)
        .where(SugarReading.user_id == user_id)
        .where(SugarReading.measured_at >= cutoff_date)
        .order_by(SugarReading.measured_at)
    )
    readings = result.scalars().all()
    
    # Format for charts
    data_points = []
    for r in readings:
        data_points.append({
            "date": r.measured_at.strftime("%Y-%m-%d"),
            "timestamp": r.measured_at.isoformat(),
            "glucose": float(r.fasting_glucose) if r.fasting_glucose else None
        })
    
    # Calculate stats
    if readings:
        glucose_vals = [float(r.fasting_glucose) for r in readings if r.fasting_glucose]
        
        stats = {
            "avg_glucose": round(sum(glucose_vals) / len(glucose_vals), 1) if glucose_vals else None,
            "min_glucose": min(glucose_vals) if glucose_vals else None,
            "max_glucose": max(glucose_vals) if glucose_vals else None,
            "readings_count": len(readings),
            "above_100_count": sum(1 for v in glucose_vals if v > 100),
            "trend": "improving" if len(glucose_vals) >= 2 and glucose_vals[-1] < glucose_vals[0] else "stable"
        }
    else:
        stats = {
            "avg_glucose": None,
            "min_glucose": None,
            "max_glucose": None,
            "readings_count": 0,
            "above_100_count": 0,
            "trend": "no_data"
        }
    
    return {
        "data": data_points,
        "stats": stats,
        "period_days": days
    }


@router.get("/weight")
async def get_weight_trend(
    days: int = Query(90, ge=7, le=365),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get weight/BMI trend"""
    # For now, return user's current weight
    # TODO: Add weight history tracking
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user or not user.weight_kg:
        return {
            "data": [],
            "stats": {"current_weight": None, "current_bmi": None},
            "period_days": days
        }
    
    # Mock data point (in production, track weight changes over time)
    return {
        "data": [{
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "weight": float(user.weight_kg) if user.weight_kg else None,
            "bmi": float(user.bmi) if user.bmi else None
        }],
        "stats": {
            "current_weight": float(user.weight_kg) if user.weight_kg else None,
            "current_bmi": float(user.bmi) if user.bmi else None
        },
        "period_days": days
    }


@router.get("/summary")
async def get_trends_summary(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get quick summary of all trends"""
    # Last 30 days
    cutoff = datetime.utcnow() - timedelta(days=30)
    
    # BP count
    bp_result = await db.execute(
        select(func.count(BPReading.id))
        .where(BPReading.user_id == user_id)
        .where(BPReading.measured_at >= cutoff)
    )
    bp_count = bp_result.scalar() or 0
    
    # Sugar count
    sugar_result = await db.execute(
        select(func.count(SugarReading.id))
        .where(SugarReading.user_id == user_id)
        .where(SugarReading.measured_at >= cutoff)
    )
    sugar_count = sugar_result.scalar() or 0
    
    return {
        "last_30_days": {
            "bp_readings": bp_count,
            "sugar_readings": sugar_count,
            "total_logs": bp_count + sugar_count
        }
    }
