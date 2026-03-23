import numpy as np
import datetime
import json
from sqlalchemy import select, desc, delete
from sqlalchemy.ext.asyncio import AsyncSession
from models.domain import (
    User, UserDataStatus, BPReading, SugarReading, BloodReport,
    HealthSignal, PreventiveCare, DailyTask, DietRecommendation
)
from ml.preventive_care import generate_preventive_care
from ml.task_generator import generate_daily_tasks
from ml.diet_engine import generate_diet_plan

async def get_user(user_id: str, db: AsyncSession):
    row = await db.execute(select(User).where(User.id == user_id))
    return row.scalar_one_or_none()

async def get_data_status(user_id: str, db: AsyncSession):
    row = await db.execute(select(UserDataStatus).where(UserDataStatus.user_id == user_id))
    return row.scalar_one_or_none()

async def get_bp_readings_7d(user_id: str, db: AsyncSession):
    row = await db.execute(
        select(BPReading)
        .where(BPReading.user_id == user_id)
        .order_by(desc(BPReading.date))
        .limit(7)
    )
    return row.scalars().all()

async def get_sugar_readings_4w(user_id: str, db: AsyncSession):
    row = await db.execute(
        select(SugarReading)
        .where(SugarReading.user_id == user_id)
        .order_by(desc(SugarReading.date))
        .limit(4)
    )
    return row.scalars().all()

async def get_latest_report(user_id: str, db: AsyncSession):
    row = await db.execute(
        select(BloodReport)
        .where(BloodReport.user_id == user_id)
        .order_by(desc(BloodReport.uploaded_at))
        .limit(1)
    )
    return row.scalar_one_or_none()

def build_features(user, bp_readings, sugar_readings, report):
    f = {}
    
    # Calculate actual age
    if user.date_of_birth:
        today = datetime.date.today()
        dob = user.date_of_birth
        f["age"] = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    else:
        f["age"] = 35 # Fallback
        
    f["gender_enc"] = 1 if user.gender == "male" else 0
    f["bmi"] = float(user.bmi or 23.0)
    f["height_cm"] = float(user.height_cm or 170.0)
    f["weight_kg"] = float(user.weight_kg or 70.0)
    f["waist_cm"] = float(user.waist_cm or 85.0)
    f["smoking"] = int(user.smoking or 0)
    f["alcohol"] = int(user.alcohol or 0)
    f["activity_level"] = user.activity_level or 1.0
    f["stress_level"] = user.stress_level or 3.0
    f["family_hx_diabetes"] = int(user.family_hx_diabetes or 0)
    f["family_hx_heart"] = int(user.family_hx_heart or 0)

    if bp_readings:
        sys_vals = [r.systolic for r in bp_readings]
        f["systolic_avg_7d"] = round(sum(sys_vals)/len(sys_vals), 1)
        f["systolic_trend"] = 0.1 # Simplified
    else:
        f["systolic_avg_7d"] = 0
        f["systolic_trend"] = 0

    if sugar_readings:
        sg_vals = [r.fasting_glucose for r in sugar_readings]
        f["fasting_sugar_avg"] = round(sum(sg_vals)/len(sg_vals), 1)
        f["sugar_readings_above_100"] = sum(1 for s in sg_vals if s > 100)
    else:
        f["fasting_sugar_avg"] = 0
        f["sugar_readings_above_100"] = 0

    if report:
        f["hemoglobin"] = float(report.hemoglobin or 0)
        f["platelet_count"] = int(report.platelet_count or 0)
    else:
        f["hemoglobin"] = 0
        f["platelet_count"] = 0
    
    return f

async def save_preventive_care(user_id: str, care_items: list[dict], db: AsyncSession):
    await db.execute(delete(PreventiveCare).where(PreventiveCare.user_id == user_id))
    for item in care_items:
        obj = PreventiveCare(
            user_id=user_id,
            category=item["category"],
            urgency=item["urgency"],
            current_value=item["current_status"],
            future_risk_message=item["future_risk_message"],
            prevention_steps=json.dumps(item["prevention_steps"]),
            risk_horizon=item["risk_horizon"]
        )
        db.add(obj)

async def replace_todays_tasks(user_id: str, task_list: list[dict], db: AsyncSession):
    await db.execute(
        delete(DailyTask)
        .where(DailyTask.user_id == user_id)
        .where(DailyTask.completed == False)
        .where(DailyTask.task_date == datetime.date.today())
    )
    for t in task_list:
        obj = DailyTask(
            user_id=user_id,
            task_type=t["task_type"],
            task_name=t["task_name"],
            description=t["description"],
            why_this_task=t["why_this_task"],
            category=t["category"],
            time_of_day=t["time_of_day"],
            duration_or_quantity=t["duration_or_quantity"],
            coins_reward=t["coins_reward"],
            task_date=datetime.date.today()
        )
        db.add(obj)

async def save_diet(user_id: str, diet: dict, db: AsyncSession):
    await db.execute(delete(DietRecommendation).where(DietRecommendation.user_id == user_id))
    obj = DietRecommendation(
        user_id=user_id,
        focus_type=diet["focus_type"],
        reason=diet["reason"],
        eat_more=json.dumps(diet["eat_more"]),
        reduce=json.dumps(diet["reduce"]),
        avoid=json.dumps(diet["avoid"]),
        hydration_goal_glasses=diet["hydration_goal"]
    )
    db.add(obj)

async def update_analysis_status(user_id: str, db: AsyncSession):
    result = await db.execute(select(UserDataStatus).where(UserDataStatus.user_id == user_id))
    status = result.scalar_one_or_none()
    if status:
        status.last_analysis_at = datetime.datetime.utcnow()
        status.analysis_ready = True

async def run_full_analysis(user_id: str, db: AsyncSession):
    user = await get_user(user_id, db)
    if not user: return None
    bp_readings = await get_bp_readings_7d(user_id, db)
    sugar_readings = await get_sugar_readings_4w(user_id, db)
    latest_report = await get_latest_report(user_id, db)

    features = build_features(user, bp_readings, sugar_readings, latest_report)
    signals = {}
    
    preventive = generate_preventive_care(features, signals)
    tasks = generate_daily_tasks(features, signals, user)
    diet = generate_diet_plan(features, signals)

    await save_preventive_care(user_id, preventive, db)
    await replace_todays_tasks(user_id, tasks, db)
    await save_diet(user_id, diet, db)
    await update_analysis_status(user_id, db)
    
    await db.commit()
    return {"preventive_care": preventive, "tasks": tasks, "diet": diet}
