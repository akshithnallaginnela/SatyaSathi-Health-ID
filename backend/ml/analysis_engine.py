"""
VitalID Analysis Engine V5 — FUTURE PREVENTIVE CARE + PRESENT DAILY TASKS
Data sources: BP readings, Sugar readings, Blood Report (Hb, Platelets, Glucose, etc.), BMI

DESIGN RULES:
1. Preventive Care = FUTURE risk predictions (what WILL happen if not addressed)
2. Daily Tasks = PRESENT actions the user should do TODAY
3. Tasks ONLY generated when user has actual vitals data
4. Positive framing — encouraging, never alarming
5. Tasks update every time new data comes in
"""
import datetime
import json
import math
from sqlalchemy import select, desc, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from models.domain import (
    User, UserDataStatus, BPReading, SugarReading, BloodReport,
    HealthSignal, PreventiveCare, DailyTask, DietRecommendation
)


# ════════════════════════════════════════════════════════════════
# 1. DATA COLLECTION
# ════════════════════════════════════════════════════════════════

async def get_user(user_id: str, db: AsyncSession):
    row = await db.execute(select(User).where(User.id == user_id))
    return row.scalar_one_or_none()

async def get_data_status(user_id: str, db: AsyncSession):
    row = await db.execute(select(UserDataStatus).where(UserDataStatus.user_id == user_id))
    return row.scalar_one_or_none()

async def get_bp_readings(user_id: str, db: AsyncSession, limit=30):
    row = await db.execute(
        select(BPReading).where(BPReading.user_id == user_id)
        .order_by(desc(BPReading.measured_at)).limit(limit)
    )
    return row.scalars().all()

async def get_sugar_readings(user_id: str, db: AsyncSession, limit=30):
    row = await db.execute(
        select(SugarReading).where(SugarReading.user_id == user_id)
        .order_by(desc(SugarReading.measured_at)).limit(limit)
    )
    return row.scalars().all()

async def get_latest_report(user_id: str, db: AsyncSession):
    row = await db.execute(
        select(BloodReport).where(BloodReport.user_id == user_id)
        .order_by(desc(BloodReport.uploaded_at)).limit(1)
    )
    return row.scalar_one_or_none()
