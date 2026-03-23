"""
VitalID Analysis Engine V3 — FULL DATA FUSION
Considers ALL sources: BP, Sugar, BMI, Weight, Height, Blood Reports, Age, 
Lifestyle (smoking, alcohol, stress, activity), Family history.
Generates: Preventive Care, Daily Tasks, Diet Plan, Health Index Score.
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
# 1. DATA COLLECTION — Gather ALL user health data
# ════════════════════════════════════════════════════════════════

async def get_user(user_id: str, db: AsyncSession):
    row = await db.execute(select(User).where(User.id == user_id))
    return row.scalar_one_or_none()

async def get_data_status(user_id: str, db: AsyncSession):
    row = await db.execute(select(UserDataStatus).where(UserDataStatus.user_id == user_id))
    return row.scalar_one_or_none()

async def get_bp_readings(user_id: str, db: AsyncSession, limit=30):
    row = await db.execute(
        select(BPReading)
        .where(BPReading.user_id == user_id)
        .order_by(desc(BPReading.date))
        .limit(limit)
    )
    return row.scalars().all()

async def get_sugar_readings(user_id: str, db: AsyncSession, limit=30):
    row = await db.execute(
        select(SugarReading)
        .where(SugarReading.user_id == user_id)
        .order_by(desc(SugarReading.date))
        .limit(limit)
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


# ════════════════════════════════════════════════════════════════
# 2. FEATURE EXTRACTION — Build unified health profile
# ════════════════════════════════════════════════════════════════

def build_features(user, bp_readings, sugar_readings, report) -> dict:
    """
    Build a comprehensive feature dictionary from ALL available data.
    Every field defaults to None so downstream engines know what data exists.
    """
    f = {}
    
    # ── Demographics ──
    if user.date_of_birth:
        today = datetime.date.today()
        dob = user.date_of_birth
        f["age"] = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    else:
        f["age"] = None
    
    f["gender"] = user.gender or "unknown"
    f["gender_enc"] = 1 if f["gender"] == "male" else 0
    
    # ── Anthropometrics (BMI, Weight, Height) ──
    f["weight_kg"] = float(user.weight_kg) if user.weight_kg else None
    f["height_cm"] = float(user.height_cm) if user.height_cm else None
    f["waist_cm"] = float(user.waist_cm) if user.waist_cm else None
    
    if f["weight_kg"] and f["height_cm"] and f["height_cm"] > 0:
        f["bmi"] = round(f["weight_kg"] / ((f["height_cm"] / 100) ** 2), 2)
    else:
        f["bmi"] = float(user.bmi) if user.bmi else None
    
    # BMI classification
    if f["bmi"]:
        if f["bmi"] < 18.5:
            f["bmi_class"] = "underweight"
        elif f["bmi"] < 25:
            f["bmi_class"] = "normal"
        elif f["bmi"] < 30:
            f["bmi_class"] = "overweight"
        else:
            f["bmi_class"] = "obese"
    else:
        f["bmi_class"] = None
    
    # ── Lifestyle Flags ──
    f["smoking"] = bool(user.smoking)
    f["alcohol"] = bool(user.alcohol)
    f["activity_level"] = user.activity_level or 1  # 1-5
    f["stress_level"] = user.stress_level or 5      # 1-10
    f["family_hx_diabetes"] = bool(user.family_hx_diabetes)
    f["family_hx_heart"] = bool(user.family_hx_heart)
    
    # ── Blood Pressure Analysis ──
    if bp_readings and len(bp_readings) > 0:
        sys_vals = [r.systolic for r in bp_readings if r.systolic]
        dia_vals = [r.diastolic for r in bp_readings if r.diastolic]
        
        if sys_vals:
            f["bp_systolic_avg"] = round(sum(sys_vals) / len(sys_vals), 1)
            f["bp_systolic_latest"] = sys_vals[0]
            f["bp_systolic_min"] = min(sys_vals)
            f["bp_systolic_max"] = max(sys_vals)
            f["bp_readings_count"] = len(sys_vals)
            
            # Trend: compare first half avg vs second half avg
            if len(sys_vals) >= 4:
                mid = len(sys_vals) // 2
                recent = sum(sys_vals[:mid]) / mid
                older = sum(sys_vals[mid:]) / (len(sys_vals) - mid)
                diff = recent - older
                if diff > 3:
                    f["bp_trend"] = "rising"
                elif diff < -3:
                    f["bp_trend"] = "falling"
                else:
                    f["bp_trend"] = "stable"
                f["bp_trend_velocity"] = round(diff, 1)
            else:
                f["bp_trend"] = "insufficient_data"
                f["bp_trend_velocity"] = 0
            
            # Days above 130
            f["bp_days_above_130"] = sum(1 for v in sys_vals if v >= 130)
            f["bp_days_above_140"] = sum(1 for v in sys_vals if v >= 140)
        else:
            f["bp_systolic_avg"] = None
            
        if dia_vals:
            f["bp_diastolic_avg"] = round(sum(dia_vals) / len(dia_vals), 1)
            f["bp_diastolic_latest"] = dia_vals[0]
        else:
            f["bp_diastolic_avg"] = None
    else:
        f["bp_systolic_avg"] = None
        f["bp_diastolic_avg"] = None
        f["bp_readings_count"] = 0
        f["bp_trend"] = None
    
    # ── Blood Sugar Analysis ──
    if sugar_readings and len(sugar_readings) > 0:
        sg_vals = [r.fasting_glucose for r in sugar_readings if r.fasting_glucose]
        
        if sg_vals:
            f["sugar_avg"] = round(sum(sg_vals) / len(sg_vals), 1)
            f["sugar_latest"] = sg_vals[0]
            f["sugar_min"] = min(sg_vals)
            f["sugar_max"] = max(sg_vals)
            f["sugar_readings_count"] = len(sg_vals)
            f["sugar_above_100_count"] = sum(1 for v in sg_vals if v > 100)
            f["sugar_above_126_count"] = sum(1 for v in sg_vals if v >= 126)
            
            # Trend
            if len(sg_vals) >= 4:
                mid = len(sg_vals) // 2
                recent = sum(sg_vals[:mid]) / mid
                older = sum(sg_vals[mid:]) / (len(sg_vals) - mid)
                diff = recent - older
                if diff > 5:
                    f["sugar_trend"] = "rising"
                elif diff < -5:
                    f["sugar_trend"] = "falling"
                else:
                    f["sugar_trend"] = "stable"
                f["sugar_trend_velocity"] = round(diff, 1)
            else:
                f["sugar_trend"] = "insufficient_data"
                f["sugar_trend_velocity"] = 0
        else:
            f["sugar_avg"] = None
    else:
        f["sugar_avg"] = None
        f["sugar_readings_count"] = 0
        f["sugar_trend"] = None
    
    # ── Blood Report Values ──
    if report:
        f["hemoglobin"] = float(report.hemoglobin) if report.hemoglobin else None
        f["rbc_count"] = float(report.rbc_count) if report.rbc_count else None
        f["wbc_count"] = int(report.wbc_count) if report.wbc_count else None
        f["platelet_count"] = int(report.platelet_count) if report.platelet_count else None
        f["fasting_glucose_report"] = float(report.fasting_glucose) if report.fasting_glucose else None
        f["creatinine"] = float(report.creatinine) if report.creatinine else None
        f["urea"] = float(report.urea) if report.urea else None
        f["has_report"] = True
    else:
        f["hemoglobin"] = None
        f["platelet_count"] = None
        f["has_report"] = False
    
    return f


# ════════════════════════════════════════════════════════════════
# 3. HEALTH INDEX CALCULATOR — 0 to 100 score from ALL data
# ════════════════════════════════════════════════════════════════

def calculate_health_index(features: dict) -> int:
    """
    Calculate a 0-100 health index based on ALL available data.
    Uses penalty-based scoring: start at 100, deduct for anomalies.
    """
    score = 100.0
    data_sources = 0  # Track how many data sources we have
    
    # ── BP Score (max -30 penalty) ──
    bp_avg = features.get("bp_systolic_avg")
    if bp_avg is not None:
        data_sources += 1
        if bp_avg < 120:
            pass  # Perfect
        elif bp_avg < 130:
            score -= 8   # Elevated
        elif bp_avg < 140:
            score -= 18  # Stage 1
        elif bp_avg < 160:
            score -= 28  # Stage 2
        else:
            score -= 35  # Crisis
        
        # Trend penalty
        if features.get("bp_trend") == "rising":
            score -= 5
    
    # ── Sugar Score (max -30 penalty) ──
    sugar_avg = features.get("sugar_avg")
    if sugar_avg is not None:
        data_sources += 1
        if sugar_avg < 100:
            pass  # Normal
        elif sugar_avg < 126:
            score -= 12  # Pre-diabetic
        elif sugar_avg < 200:
            score -= 25  # Diabetic range
        else:
            score -= 35  # Severe
        
        if features.get("sugar_trend") == "rising":
            score -= 5
    
    # ── BMI Score (max -15 penalty) ──
    bmi = features.get("bmi")
    if bmi is not None:
        data_sources += 1
        if 18.5 <= bmi <= 24.9:
            pass
        elif 25 <= bmi <= 29.9:
            score -= 8
        elif bmi >= 30:
            score -= 15
        elif bmi < 18.5:
            score -= 10
    
    # ── Report Values (max -20 penalty) ──
    hb = features.get("hemoglobin")
    if hb is not None:
        data_sources += 1
        hb_low = 13.5 if features.get("gender_enc") == 1 else 12.0
        if hb < hb_low - 2:
            score -= 12
        elif hb < hb_low:
            score -= 6
    
    platelets = features.get("platelet_count")
    if platelets is not None:
        if platelets < 100000:
            score -= 15
        elif platelets < 150000:
            score -= 8
    
    # ── Lifestyle Penalties (max -15) ──
    if features.get("smoking"):
        score -= 8
        data_sources += 1
    if features.get("alcohol"):
        score -= 5
    if features.get("stress_level", 5) >= 8:
        score -= 5
    if features.get("activity_level", 3) <= 1:
        score -= 5
    
    # ── Family History Risk (max -5) ──
    if features.get("family_hx_diabetes"):
        score -= 3
    if features.get("family_hx_heart"):
        score -= 3
    
    # If NO data at all, return 0 to show empty state
    if data_sources == 0:
        return 0
    
    return max(0, min(100, round(score)))


# ════════════════════════════════════════════════════════════════
# 4. PREVENTIVE CARE — Future risk predictions from ALL data
# ════════════════════════════════════════════════════════════════

def generate_preventive_care(features: dict) -> list[dict]:
    """
    Generate preventive care items considering ALL data sources:
    BP, Sugar, BMI, Reports, Lifestyle, Family History.
    Each item predicts FUTURE risk and gives prevention steps.
    """
    care_items = []
    
    # ── BP Preventive Care ──
    bp_avg = features.get("bp_systolic_avg")
    if bp_avg is not None:
        bp_trend = features.get("bp_trend", "stable")
        days_130 = features.get("bp_days_above_130", 0)
        
        if bp_avg < 120 and bp_trend != "rising":
            care_items.append({
                "category": "blood_pressure",
                "urgency": "maintain",
                "current_status": f"Normal ({bp_avg:.0f} mmHg avg)",
                "future_risk_message": (
                    "Your BP is healthy. However, "
                    + ("with family history of heart disease, " if features.get("family_hx_heart") else "")
                    + ("and high stress levels, " if features.get("stress_level", 0) >= 7 else "")
                    + "maintaining this requires consistent habits."
                ),
                "prevention_steps": [
                    "Keep daily sodium below 2300mg",
                    "Walk at least 30 minutes, 4 days/week",
                    "Manage stress — #1 hidden BP driver",
                    "Stay hydrated — 8 glasses minimum"
                ],
                "risk_horizon": "5–10 years if lifestyle unchanged"
            })
        elif 120 <= bp_avg < 130:
            care_items.append({
                "category": "blood_pressure",
                "urgency": "watch",
                "current_status": f"Elevated ({bp_avg:.0f} mmHg avg, trend: {bp_trend})",
                "future_risk_message": (
                    f"Your BP is in the elevated zone. "
                    f"If {bp_trend}, it may move to hypertension in 4–6 weeks. "
                    "The good news — this is fully reversible with lifestyle changes."
                ),
                "prevention_steps": [
                    "Cut added salt from meals this week",
                    "Walk 30 min daily — reduces BP by 5–8 mmHg",
                    "Reduce caffeine to 1 cup/day",
                    "Practice 5-min deep breathing every evening",
                    "Avoid late-night heavy meals"
                ],
                "risk_horizon": "4–6 weeks if no action"
            })
        elif bp_avg >= 130:
            care_items.append({
                "category": "blood_pressure",
                "urgency": "act_now",
                "current_status": f"High ({bp_avg:.0f} mmHg avg, {days_130} readings above 130)",
                "future_risk_message": (
                    f"Your BP has been consistently above 130. "
                    f"Trend is {bp_trend}. "
                    "If untreated, this significantly increases risk of heart attack and stroke. "
                    "Acting now can reverse this completely."
                ),
                "prevention_steps": [
                    "Stop added salt completely for 2 weeks",
                    "Walk 10,000 steps daily — start today",
                    "No alcohol this week",
                    "Sleep before 10:30 PM",
                    "Log BP every morning to track progress",
                    "Book a routine checkup if no improvement in 10 days"
                ],
                "risk_horizon": "2–3 weeks — needs immediate attention"
            })
    
    # ── Sugar Preventive Care ──
    sugar_avg = features.get("sugar_avg")
    if sugar_avg is not None:
        sugar_trend = features.get("sugar_trend", "stable")
        above_100 = features.get("sugar_above_100_count", 0)
        
        if sugar_avg < 100 and above_100 == 0:
            care_items.append({
                "category": "blood_sugar",
                "urgency": "maintain",
                "current_status": f"Normal ({sugar_avg:.0f} mg/dL avg)",
                "future_risk_message": (
                    "Your fasting sugar is healthy. "
                    + ("With family history of diabetes, " if features.get("family_hx_diabetes") else "")
                    + "watch carb intake as you age."
                ),
                "prevention_steps": [
                    "Avoid sugary drinks — even fruit juice",
                    "Walk 10 min after every major meal",
                    "Include protein with every meal",
                    "Get sugar checked every 3 months"
                ],
                "risk_horizon": "Long-term maintenance"
            })
        elif 100 <= sugar_avg < 126 or above_100 >= 2:
            care_items.append({
                "category": "blood_sugar",
                "urgency": "watch",
                "current_status": f"Pre-diabetic ({sugar_avg:.0f} mg/dL avg, {above_100} readings above 100)",
                "future_risk_message": (
                    f"Your fasting sugar is in the pre-diabetic range (trend: {sugar_trend}). "
                    "Research shows lifestyle changes at this stage can fully "
                    "reverse the trend in 8–12 weeks."
                ),
                "prevention_steps": [
                    "Replace white rice with brown rice/millets",
                    "Eliminate sugar from tea and coffee",
                    "Walk 30 min every morning before breakfast",
                    "Eat dinner before 7:30 PM",
                    "Eat whole fruits instead of juices",
                    "Get HbA1c tested for 3-month sugar picture"
                ],
                "risk_horizon": "8–12 weeks to reverse"
            })
        elif sugar_avg >= 126:
            care_items.append({
                "category": "blood_sugar",
                "urgency": "act_now",
                "current_status": f"Elevated ({sugar_avg:.0f} mg/dL avg)",
                "future_risk_message": (
                    "Your fasting sugar is consistently above 126 mg/dL. "
                    "This pattern needs medical evaluation and HbA1c test."
                ),
                "prevention_steps": [
                    "Visit a doctor for HbA1c test this week",
                    "Stop all sugary foods completely",
                    "Walk 45 min daily — morning is best",
                    "Log sugar every day this week",
                    "Eat small meals every 3 hours"
                ],
                "risk_horizon": "Immediate — doctor visit recommended"
            })
    
    # ── BMI Preventive Care ──
    bmi = features.get("bmi")
    if bmi is not None:
        bmi_class = features.get("bmi_class", "normal")
        weight = features.get("weight_kg", 0)
        
        if bmi_class == "overweight":
            care_items.append({
                "category": "weight_bmi",
                "urgency": "watch",
                "current_status": f"Overweight (BMI {bmi}, Weight {weight:.0f}kg)",
                "future_risk_message": (
                    f"Your BMI of {bmi} puts you in the overweight range. "
                    "This increases risk of diabetes, heart disease, and joint problems. "
                    "Losing 3-5 kg can reduce BP by 5 mmHg and sugar by 10-15 mg/dL."
                ),
                "prevention_steps": [
                    "Reduce portion sizes by 20%",
                    "Walk 10,000 steps daily",
                    "Cut fried foods to twice a week",
                    "Eat more vegetables with every meal",
                    "Track weight weekly — aim for 0.5 kg/week loss"
                ],
                "risk_horizon": "3–6 months for healthy BMI"
            })
        elif bmi_class == "obese":
            care_items.append({
                "category": "weight_bmi",
                "urgency": "act_now",
                "current_status": f"Obese (BMI {bmi}, Weight {weight:.0f}kg)",
                "future_risk_message": (
                    f"Your BMI of {bmi} significantly increases risk of "
                    "type 2 diabetes, cardiovascular disease, and sleep apnea. "
                    "Medical consultation is recommended alongside lifestyle changes."
                ),
                "prevention_steps": [
                    "Consult a doctor for weight management plan",
                    "Start with 20-min daily walks, increase gradually",
                    "Eliminate sugary and fried foods completely",
                    "Eat protein-rich breakfast to reduce cravings",
                    "Sleep 7-8 hours — poor sleep causes weight gain"
                ],
                "risk_horizon": "Immediate lifestyle intervention needed"
            })
    
    # ── Hemoglobin Preventive Care ──
    hb = features.get("hemoglobin")
    if hb is not None:
        gender_enc = features.get("gender_enc", 1)
        hb_low = 13.5 if gender_enc == 1 else 12.0
        
        if hb < hb_low - 1.5:
            care_items.append({
                "category": "hemoglobin",
                "urgency": "act_now",
                "current_status": f"Low hemoglobin ({hb} g/dL)",
                "future_risk_message": (
                    "Your hemoglobin is significantly below normal, causing fatigue "
                    "and reduced immunity. Usually iron deficiency — very treatable."
                ),
                "prevention_steps": [
                    "See a doctor to confirm cause",
                    "Eat iron-rich foods: spinach, lentils, dates, jaggery",
                    "Take iron supplement if doctor advises",
                    "Eat vitamin C with iron foods for better absorption",
                    "Avoid tea/coffee 1 hour after iron-rich meals"
                ],
                "risk_horizon": "6 weeks to see improvement"
            })
        elif hb < hb_low:
            care_items.append({
                "category": "hemoglobin",
                "urgency": "watch",
                "current_status": f"Slightly low hemoglobin ({hb} g/dL)",
                "future_risk_message": (
                    "Your hemoglobin is slightly below normal. You may feel mild fatigue. "
                    "Dietary changes can improve this in 6-8 weeks."
                ),
                "prevention_steps": [
                    "Increase iron-rich foods: spinach, dal, eggs",
                    "Add jaggery or dates as snacks",
                    "Eat citrus fruit daily — boosts iron absorption",
                    "Reduce tea/coffee — blocks iron absorption"
                ],
                "risk_horizon": "8 weeks with dietary changes"
            })
    
    # ── Platelet Preventive Care ──
    platelets = features.get("platelet_count")
    if platelets is not None and platelets > 0:
        if platelets < 100000:
            care_items.append({
                "category": "platelets",
                "urgency": "act_now",
                "current_status": f"Low platelets ({platelets:,}/cumm)",
                "future_risk_message": (
                    "Significantly below normal (150,000-410,000). "
                    "Increases bleeding risk and needs medical evaluation."
                ),
                "prevention_steps": [
                    "See a doctor within the next few days",
                    "Avoid aspirin and ibuprofen",
                    "Eat papaya and pomegranate",
                    "Stay hydrated — 10+ glasses daily",
                    "Report any unusual bruising"
                ],
                "risk_horizon": "Immediate medical evaluation"
            })
        elif platelets < 150000:
            care_items.append({
                "category": "platelets",
                "urgency": "watch",
                "current_status": f"Borderline low platelets ({platelets:,})",
                "future_risk_message": (
                    "Borderline-low range. Retest in 2-3 weeks to confirm."
                ),
                "prevention_steps": [
                    "Retest CBC in 2-3 weeks",
                    "Eat papaya leaf extract",
                    "Include pomegranate and green leafy vegetables",
                    "Avoid alcohol completely"
                ],
                "risk_horizon": "Retest in 2-3 weeks"
            })
    
    # ── Combined Risk: Smoking + High BP ──
    if features.get("smoking") and bp_avg and bp_avg >= 120:
        care_items.append({
            "category": "lifestyle_compound",
            "urgency": "act_now",
            "current_status": "Smoking + Elevated BP — High cardiac risk",
            "future_risk_message": (
                "Smoking combined with elevated blood pressure "
                "multiplies your risk of heart attack by 4-6x. "
                "Quitting smoking alone can reduce BP by 5-10 mmHg."
            ),
            "prevention_steps": [
                "Reduce smoking by 2 cigarettes/day this week",
                "Set a quit date within 30 days",
                "Try nicotine patches or gum",
                "Walk daily to manage cravings",
                "Tell a friend about your quit plan for accountability"
            ],
            "risk_horizon": "Ongoing — every day without smoking helps"
        })
    
    # ── Combined Risk: Family History + Pre-diabetic Sugar ──
    if features.get("family_hx_diabetes") and sugar_avg and sugar_avg >= 90:
        care_items.append({
            "category": "genetic_risk",
            "urgency": "watch",
            "current_status": "Family diabetes history + borderline sugar",
            "future_risk_message": (
                "With a family history of diabetes and fasting sugar "
                f"at {sugar_avg:.0f} mg/dL, you have a higher genetic predisposition. "
                "Early lifestyle intervention is highly effective."
            ),
            "prevention_steps": [
                "Get HbA1c tested every 6 months",
                "Post-meal walks are critical for you",
                "Focus on low-GI foods: oats, brown rice, millets",
                "Monitor weight closely — even 3 kg loss helps"
            ],
            "risk_horizon": "Ongoing monitoring recommended"
        })
    
    # ── If NO data, add a base message ──
    if not care_items:
        care_items.append({
            "category": "general",
            "urgency": "info",
            "current_status": "No health data yet",
            "future_risk_message": (
                "Start by logging your Blood Pressure, Blood Sugar, or uploading "
                "a blood report. The more data we have, the better your preventive insights."
            ),
            "prevention_steps": [
                "Log your morning blood pressure",
                "Record your fasting blood sugar",
                "Upload a recent blood report",
                "Keep tracking daily for better predictions"
            ],
            "risk_horizon": "Start tracking to see predictions"
        })
    
    return care_items


# ════════════════════════════════════════════════════════════════
# 5. DAILY TASK GENERATION — Dynamic from ALL data
# ════════════════════════════════════════════════════════════════

def generate_daily_tasks(features: dict, user) -> list[dict]:
    """
    Generate tasks based on ALL health data — not just reports.
    Always includes base tasks + condition-specific tasks.
    """
    tasks = []
    
    # ── ALWAYS: Hydration ──
    tasks.append({
        "task_type": "WATER_INTAKE",
        "task_name": "Drink 8 glasses of water",
        "description": "Stay hydrated throughout the day",
        "why_this_task": "Hydration supports kidney function, blood pressure, and overall health",
        "category": "wellness",
        "time_of_day": "all_day",
        "duration_or_quantity": "8 glasses (250ml each)",
        "coins_reward": 8
    })
    
    # ── ALWAYS: Log BP ──
    tasks.append({
        "task_type": "LOG_BP",
        "task_name": "Log your morning BP",
        "description": "Take and record your blood pressure",
        "why_this_task": "Tracking BP trends is how we spot problems before they develop",
        "category": "vitals",
        "time_of_day": "morning",
        "duration_or_quantity": "2 minute task",
        "coins_reward": 15
    })
    
    # ── BP-Based Tasks ──
    bp_avg = features.get("bp_systolic_avg")
    if bp_avg is not None:
        if bp_avg >= 130:
            tasks.append({
                "task_type": "MORNING_WALK",
                "task_name": "Walk 10,000 steps today",
                "description": "Brisk walking for at least 30 minutes",
                "why_this_task": f"Your BP avg is {bp_avg:.0f}. Walking reduces BP by 5-8 mmHg in 2 weeks",
                "category": "exercise",
                "time_of_day": "morning",
                "duration_or_quantity": "30 min / 10,000 steps",
                "coins_reward": 20
            })
            tasks.append({
                "task_type": "LOW_SALT_MEAL",
                "task_name": "Eat a low-salt meal today",
                "description": "Avoid pickles, packaged food, extra salt",
                "why_this_task": f"Your BP is elevated ({bp_avg:.0f}). Sodium is #1 dietary cause of high BP",
                "category": "diet",
                "time_of_day": "afternoon",
                "duration_or_quantity": "All meals today",
                "coins_reward": 10
            })
        elif bp_avg >= 120:
            tasks.append({
                "task_type": "MORNING_WALK",
                "task_name": "Walk 7,000 steps today",
                "description": "Moderate daily walking",
                "why_this_task": f"Your BP is slightly elevated ({bp_avg:.0f}). Regular walking prevents progression",
                "category": "exercise",
                "time_of_day": "morning",
                "duration_or_quantity": "25 min / 7,000 steps",
                "coins_reward": 15
            })
        else:
            tasks.append({
                "task_type": "MORNING_WALK",
                "task_name": "Walk 5,000 steps today",
                "description": "Maintain active lifestyle",
                "why_this_task": "Your BP is great! Walking keeps it that way",
                "category": "exercise",
                "time_of_day": "morning",
                "duration_or_quantity": "20 min / 5,000 steps",
                "coins_reward": 12
            })
    
    # ── Sugar-Based Tasks ──
    sugar_avg = features.get("sugar_avg")
    if sugar_avg is not None:
        tasks.append({
            "task_type": "LOG_SUGAR",
            "task_name": "Log your fasting sugar",
            "description": "Measure before breakfast",
            "why_this_task": "Weekly tracking shows your sugar trend for the preventive engine",
            "category": "vitals",
            "time_of_day": "morning",
            "duration_or_quantity": "Before breakfast",
            "coins_reward": 15
        })
        
        if sugar_avg >= 100:
            tasks.append({
                "task_type": "POST_MEAL_WALK",
                "task_name": "Walk 10 min after lunch",
                "description": "Short walk immediately after eating",
                "why_this_task": f"Your sugar avg is {sugar_avg:.0f}. Post-meal walking reduces spike by 22%",
                "category": "exercise",
                "time_of_day": "afternoon",
                "duration_or_quantity": "10 minutes",
                "coins_reward": 10
            })
            tasks.append({
                "task_type": "NO_SUGAR_DAY",
                "task_name": "No added sugar today",
                "description": "Skip sugar in tea, coffee, and snacks",
                "why_this_task": f"Fasting glucose is {sugar_avg:.0f} mg/dL. Reducing sugar intake can lower it by 8-12 mg/dL in 3 weeks",
                "category": "diet",
                "time_of_day": "all_day",
                "duration_or_quantity": "All day",
                "coins_reward": 12
            })
    
    # ── BMI-Based Tasks ──
    bmi = features.get("bmi")
    if bmi is not None and bmi > 27:
        tasks.append({
            "task_type": "LIGHT_EXERCISE",
            "task_name": "30-min exercise session",
            "description": "Walk, yoga, or stretching",
            "why_this_task": f"Your BMI is {bmi}. Reducing BMI by 1 point improves BP, sugar, and cholesterol",
            "category": "exercise",
            "time_of_day": "morning",
            "duration_or_quantity": "30 minutes",
            "coins_reward": 15
        })
    
    # ── Report-Based Tasks ──
    hb = features.get("hemoglobin")
    if hb is not None:
        hb_low = 13.5 if features.get("gender_enc") == 1 else 12.0
        if hb < hb_low:
            tasks.append({
                "task_type": "IRON_RICH_MEAL",
                "task_name": "Eat an iron-rich meal today",
                "description": "Spinach dal, chicken curry, or egg bhurji",
                "why_this_task": f"Your hemoglobin is {hb} g/dL (low). Daily iron-rich foods help naturally",
                "category": "diet",
                "time_of_day": "lunch",
                "duration_or_quantity": "At least 1 iron-rich meal",
                "coins_reward": 10
            })
    
    platelets = features.get("platelet_count")
    if platelets is not None and 0 < platelets < 150000:
        tasks.append({
            "task_type": "EAT_PAPAYA",
            "task_name": "Eat papaya today",
            "description": "Include fresh papaya in your diet",
            "why_this_task": f"Your platelets are at {platelets:,}. Papaya is traditionally linked to platelet support",
            "category": "diet",
            "time_of_day": "afternoon",
            "duration_or_quantity": "1 bowl fresh papaya",
            "coins_reward": 8
        })
    
    # ── Stress-Based Tasks ──
    stress = features.get("stress_level", 5)
    if stress >= 7:
        tasks.append({
            "task_type": "DEEP_BREATHING",
            "task_name": "5-minute deep breathing",
            "description": "Slow belly breathing exercise",
            "why_this_task": f"Your stress level is {stress}/10. Deep breathing lowers cortisol and BP within minutes",
            "category": "wellness",
            "time_of_day": "evening",
            "duration_or_quantity": "5 minutes",
            "coins_reward": 5
        })
        tasks.append({
            "task_type": "SLEEP_EARLY",
            "task_name": "Sleep by 10:30 PM tonight",
            "description": "No screens after 10 PM",
            "why_this_task": "Poor sleep raises cortisol which directly increases BP and blood sugar",
            "category": "wellness",
            "time_of_day": "evening",
            "duration_or_quantity": "7-8 hours",
            "coins_reward": 10
        })
    
    # ── Medication Tasks ──
    if hasattr(user, 'medications') and user.medications:
        try:
            import json as _json
            meds = _json.loads(user.medications) if isinstance(user.medications, str) else user.medications
            for med in (meds or []):
                tasks.append({
                    "task_type": "MEDICATION",
                    "task_name": f"Take {med}",
                    "description": "As prescribed by your doctor",
                    "why_this_task": "Consistent medication timing ensures maximum effectiveness",
                    "category": "medication",
                    "time_of_day": "morning",
                    "duration_or_quantity": "As prescribed",
                    "coins_reward": 10
                })
        except Exception:
            pass
    
    return tasks


# ════════════════════════════════════════════════════════════════
# 6. DIET PLAN — Personalized from ALL data
# ════════════════════════════════════════════════════════════════

def generate_diet_plan(features: dict) -> dict:
    """Generate a personalized diet plan considering all health data."""
    
    bmi = features.get("bmi")
    bp_avg = features.get("bp_systolic_avg")
    sugar_avg = features.get("sugar_avg")
    hb = features.get("hemoglobin")
    platelets = features.get("platelet_count")
    gender_enc = features.get("gender_enc", 1)
    hb_low = 13.5 if gender_enc == 1 else 12.0
    
    eat_more = []
    reduce = []
    avoid = []
    focus_parts = []
    reason_parts = []
    hydration = 8
    
    # ── BP-driven diet ──
    if bp_avg is not None and bp_avg >= 120:
        focus_parts.append("low_sodium")
        reason_parts.append(f"BP is elevated ({bp_avg:.0f} mmHg)")
        eat_more.extend([
            "Banana (natural potassium — counters sodium)",
            "Spinach and leafy greens",
            "Garlic (natural BP lowering effect)",
            "Oats (reduces BP over time)"
        ])
        reduce.extend(["Salt in cooking — use lemon instead", "Chai and coffee to 1 cup daily"])
        avoid.extend(["Pickles, papad, chutneys", "Packaged chips, namkeen", "Instant noodles"])
        hydration = max(hydration, 10)
    
    # ── Sugar-driven diet ──
    if sugar_avg is not None and sugar_avg >= 100:
        focus_parts.append("diabetic_friendly")
        reason_parts.append(f"Sugar is elevated ({sugar_avg:.0f} mg/dL)")
        eat_more.extend([
            "Brown rice or millets (ragi, jowar, bajra)",
            "Bitter gourd (karela) — natural sugar reducer",
            "Methi seeds — soak overnight, eat morning",
            "Nuts as snacks (almonds, walnuts)"
        ])
        reduce.extend(["White rice to half a cup", "Fruit intake to low-GI fruits only"])
        avoid.extend(["Sugar in tea/coffee", "Fruit juices (even fresh)", "Maida products"])
    
    # ── Hemoglobin-driven diet ──
    if hb is not None and hb < hb_low:
        focus_parts.append("iron_rich")
        reason_parts.append(f"Hemoglobin is low ({hb} g/dL)")
        eat_more.extend([
            "Spinach, palak, methi daily",
            "Rajma, chana, masoor dal",
            "Jaggery (gud) instead of sugar",
            "Pomegranate and beetroot"
        ])
        reduce.extend(["Tea/coffee — blocks iron absorption"])
        hydration = max(hydration, 9)
    
    # ── Platelet-driven diet ──
    if platelets is not None and 0 < platelets < 150000:
        focus_parts.append("platelet_support")
        reason_parts.append(f"Platelets are low ({platelets:,})")
        eat_more.extend([
            "Fresh papaya (whole fruit)",
            "Pomegranate seeds and juice",
            "Pumpkin and pumpkin seeds"
        ])
        avoid.extend(["Alcohol", "Aspirin without doctor advice"])
        hydration = max(hydration, 10)
    
    # ── BMI-driven diet ──
    if bmi is not None and bmi >= 27:
        focus_parts.append("weight_management")
        reason_parts.append(f"BMI is {bmi} (overweight)")
        eat_more.extend([
            "High-protein breakfast (eggs, paneer)",
            "Salads before each meal",
            "Green tea instead of milk tea"
        ])
        reduce.extend(["Portion sizes by 20%", "Fried foods to twice a week"])
        avoid.extend(["Late night snacking", "Sugary drinks and sweets"])
    
    # ── Default balanced if nothing specific ──
    if not focus_parts:
        focus_parts.append("balanced")
        reason_parts.append("Your vitals are healthy — maintain this")
        eat_more.extend([
            "Seasonal vegetables with every meal",
            "2-3 fruits daily",
            "Whole grains instead of refined",
            "Lean protein with every meal"
        ])
        reduce.extend(["Fried foods to twice a week", "Packaged and processed food"])
        avoid.extend(["Sugary drinks", "Trans fats"])
    
    # Deduplicate
    eat_more = list(dict.fromkeys(eat_more))
    reduce = list(dict.fromkeys(reduce))
    avoid = list(dict.fromkeys(avoid))
    
    return {
        "focus_type": " + ".join(focus_parts),
        "reason": ". ".join(reason_parts),
        "eat_more": eat_more,
        "reduce": reduce,
        "avoid": avoid,
        "hydration_goal": hydration
    }


# ════════════════════════════════════════════════════════════════
# 7. PERSISTENCE — Save results to DB
# ════════════════════════════════════════════════════════════════

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


# ════════════════════════════════════════════════════════════════
# 8. MAIN ENTRY — Run full analysis pipeline
# ════════════════════════════════════════════════════════════════

async def run_full_analysis(user_id: str, db: AsyncSession):
    """
    MASTER PIPELINE: Collects ALL data → Builds features → 
    Generates preventive care, tasks, diet → Saves to DB.
    Called after any vital log, report upload, or profile update.
    """
    user = await get_user(user_id, db)
    if not user:
        return None
    
    bp_readings = await get_bp_readings(user_id, db)
    sugar_readings = await get_sugar_readings(user_id, db)
    latest_report = await get_latest_report(user_id, db)
    
    # Build unified feature set from ALL data
    features = build_features(user, bp_readings, sugar_readings, latest_report)
    
    # Calculate health index from ALL data
    health_index = calculate_health_index(features)
    
    # Generate preventive care from ALL data
    preventive = generate_preventive_care(features)
    
    # Generate daily tasks from ALL data
    tasks = generate_daily_tasks(features, user)
    
    # Generate diet plan from ALL data
    diet = generate_diet_plan(features)
    
    # Persist everything
    await save_preventive_care(user_id, preventive, db)
    await replace_todays_tasks(user_id, tasks, db)
    await save_diet(user_id, diet, db)
    await update_analysis_status(user_id, db)
    
    await db.commit()
    
    return {
        "health_index": health_index,
        "preventive_care": preventive,
        "tasks": tasks,
        "diet": diet
    }
