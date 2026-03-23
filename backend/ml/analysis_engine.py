import numpy as np
import datetime
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from models.domain import (
    User, UserDataStatus, BPReading, SugarReading, BloodReport,
    HealthSignal, PreventiveCare, DailyTask, DietRecommendation
)
from ml.preventive_care import generate_preventive_care
from ml.task_generator import generate_daily_tasks
from ml.diet_engine import generate_diet_plan
# Note: In a real app, you would also import predict_signals from a trained model file.
# from ml.predict import predict_from_report

async def get_user(user_id: str, db: AsyncSession):
    row = await db.execute(select(User).where(User.id == user_id))
    return row.scalar_one_or_none()

async def get_data_status(user_id: str, db: AsyncSession):
    row = await db.execute(select(UserDataStatus).where(UserDataStatus.user_id == user_id))
    return row.scalar_one_or_none()

async def get_bp_readings_7d(user_id: str, db: AsyncSession):
    # Retrieve last 7 readings (simplified for prototype)
    row = await db.execute(
        select(BPReading)
        .where(BPReading.user_id == user_id)
        .order_by(desc(BPReading.measured_at))
        .limit(7)
    )
    return row.scalars().all()

async def get_sugar_readings_4w(user_id: str, db: AsyncSession):
    row = await db.execute(
        select(SugarReading)
        .where(SugarReading.user_id == user_id)
        .order_by(desc(SugarReading.measured_at))
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

    # Demographics
    f["age"]               = getattr(user, "age", 30) # Assuming age computed from DOB
    f["gender_enc"]        = 1 if user.gender == "male" else 0
    f["bmi"]               = user.bmi or 0
    f["waist_cm"]          = user.waist_cm or 0
    f["smoking"]           = int(user.smoking or 0)
    f["alcohol"]           = int(user.alcohol or 0)
    f["activity_level"]    = user.activity_level or 1
    f["stress_level"]      = user.stress_level or 5
    f["family_hx_diabetes"]= int(user.family_hx_diabetes or 0)
    f["family_hx_heart"]   = int(user.family_hx_heart or 0)

    # BP features (from 7-day readings)
    if bp_readings and len(bp_readings) >= 1:
        sys_vals = [r.systolic  for r in bp_readings]
        dia_vals = [r.diastolic for r in bp_readings]
        f["systolic_avg_7d"]  = round(sum(sys_vals)/len(sys_vals), 1)
        f["diastolic_avg_7d"] = round(sum(dia_vals)/len(dia_vals), 1)
        f["systolic_max_7d"]  = max(sys_vals)
        f["systolic_min_7d"]  = min(sys_vals)
        f["days_above_130"]   = sum(1 for s in sys_vals if s > 130)
        f["days_above_140"]   = sum(1 for s in sys_vals if s > 140)
        if len(sys_vals) >= 3:
            x = list(range(len(sys_vals)))
            f["systolic_trend"]  = round(float(np.polyfit(x, sys_vals, 1)[0]), 3)
            f["bp_variability"]  = round(float(np.std(sys_vals)), 2)
        else:
            f["systolic_trend"]  = 0.0
            f["bp_variability"]  = 0.0
    else:
        for k in ["systolic_avg_7d","diastolic_avg_7d",
                  "systolic_max_7d","systolic_min_7d",
                  "days_above_130","days_above_140",
                  "systolic_trend","bp_variability"]:
            f[k] = 0

    # Sugar features (from 4-week readings)
    if sugar_readings and len(sugar_readings) >= 1:
        sg_vals = [r.fasting_glucose for r in sugar_readings]
        f["fasting_sugar_avg"]        = round(sum(sg_vals)/len(sg_vals), 1)
        f["fasting_sugar_latest"]     = float(sg_vals[-1])
        f["sugar_readings_above_100"] = sum(1 for s in sg_vals if s > 100)
        f["sugar_readings_above_125"] = sum(1 for s in sg_vals if s > 125)
        if len(sg_vals) >= 2:
            x = list(range(len(sg_vals)))
            f["sugar_trend_slope"] = round(float(np.polyfit(x, sg_vals, 1)[0]), 3)
        else:
            f["sugar_trend_slope"] = 0.0
    else:
        for k in ["fasting_sugar_avg","fasting_sugar_latest",
                  "sugar_readings_above_100",
                  "sugar_readings_above_125","sugar_trend_slope"]:
            f[k] = 0

    # Report features
    if report:
        f["hemoglobin"]      = float(report.hemoglobin or 0)
        f["rbc_count"]       = float(report.rbc_count or 0)
        f["pcv"]             = float(report.pcv or 0)
        f["mcv"]             = float(report.mcv or 0)
        f["mch"]             = float(report.mch or 0)
        f["mchc"]            = float(report.mchc or 0)
        f["rdw"]             = float(report.rdw or 0)
        f["wbc_count"]       = int(report.wbc_count or 0)
        f["platelet_count"]  = int(report.platelet_count or 0)
        f["neutrophils_pct"] = float(report.neutrophils_pct or 0)
        f["lymphocytes_pct"] = float(report.lymphocytes_pct or 0)
        f["fasting_glucose"] = float(report.fasting_glucose or f.get("fasting_sugar_latest", 0))
        f["urea"]            = float(report.urea or 0)
        f["creatinine"]      = float(report.creatinine or 0)
    else:
        for k in ["hemoglobin","rbc_count","pcv","mcv","mch",
                  "mchc","rdw","wbc_count","platelet_count",
                  "neutrophils_pct","lymphocytes_pct",
                  "fasting_glucose","urea","creatinine"]:
            f[k] = 0

    # Computed urgency (rough pre-score for model)
    urgency = 0
    if f["days_above_130"] >= 3: urgency += 2
    if f["days_above_140"] >= 1: urgency += 3
    if f["fasting_sugar_avg"] > 100: urgency += 2
    if f["fasting_sugar_avg"] > 125: urgency += 3
    if f.get("hemoglobin", 14) < 12: urgency += 2
    if f.get("platelet_count", 200000) < 150000: urgency += 3
    f["urgency_score"] = min(10, urgency)

    return f


async def run_full_analysis(user_id: str, db: AsyncSession):
    """
    Triggered after every data update.
    Regenerates signals, preventive care, tasks, diet.
    """
    user   = await get_user(user_id, db)
    status = await get_data_status(user_id, db)

    bp_readings    = await get_bp_readings_7d(user_id, db)
    sugar_readings = await get_sugar_readings_4w(user_id, db)
    latest_report  = await get_latest_report(user_id, db)

    features = build_features(
        user, bp_readings, sugar_readings, latest_report
    )

    # In a real app we run ML predictions here (predict_signals)
    signals = {}
    
    preventive = generate_preventive_care(features, signals)
    tasks      = generate_daily_tasks(features, signals, user)
    diet       = generate_diet_plan(features, signals)

    # Assume dummy implementation for db saving logic for now
    # await save_signals(user_id, signals, db)
    # await save_preventive_care(user_id, preventive, db)
    # await replace_todays_tasks(user_id, tasks, db)
    # await save_diet(user_id, diet, db)
    # await update_analysis_status(user_id, db)
    # await db.commit()

    return {
        "signals": signals,
        "preventive_care": preventive,
        "tasks": tasks,
        "diet": diet
    }
