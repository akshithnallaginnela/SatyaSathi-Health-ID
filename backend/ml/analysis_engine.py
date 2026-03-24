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


# ════════════════════════════════════════════════════════════════
# 2. FEATURE EXTRACTION
# ════════════════════════════════════════════════════════════════

def build_features(user, bp_readings, sugar_readings, report) -> dict:
    f = {}

    # Demographics
    if user.date_of_birth:
        today = datetime.date.today()
        dob = user.date_of_birth
        f["age"] = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    else:
        f["age"] = None

    f["gender"] = user.gender or "unknown"
    f["gender_enc"] = 1 if f["gender"] == "male" else 0

    # Anthropometrics
    f["weight_kg"] = float(user.weight_kg) if user.weight_kg else None
    f["height_cm"] = float(user.height_cm) if user.height_cm else None
    f["waist_cm"] = float(user.waist_cm) if user.waist_cm else None

    if f["weight_kg"] and f["height_cm"] and f["height_cm"] > 0:
        f["bmi"] = round(f["weight_kg"] / ((f["height_cm"] / 100) ** 2), 2)
    else:
        f["bmi"] = float(user.bmi) if user.bmi else None

    if f["bmi"]:
        if f["bmi"] < 18.5:   f["bmi_class"] = "underweight"
        elif f["bmi"] < 25:   f["bmi_class"] = "normal"
        elif f["bmi"] < 30:   f["bmi_class"] = "overweight"
        else:                  f["bmi_class"] = "obese"
    else:
        f["bmi_class"] = None

    # Lifestyle
    f["smoking"] = bool(user.smoking)
    f["alcohol"] = bool(user.alcohol)
    f["activity_level"] = user.activity_level or 1
    f["stress_level"] = user.stress_level or 5
    f["family_hx_diabetes"] = bool(user.family_hx_diabetes)
    f["family_hx_heart"] = bool(user.family_hx_heart)

    # Blood Pressure
    f["has_bp_data"] = False
    if bp_readings:
        sys_vals = [r.systolic for r in bp_readings if r.systolic]
        dia_vals = [r.diastolic for r in bp_readings if r.diastolic]
        if sys_vals:
            f["has_bp_data"] = True
            f["bp_systolic_avg"] = round(sum(sys_vals) / len(sys_vals), 1)
            f["bp_systolic_latest"] = sys_vals[0]
            f["bp_systolic_min"] = min(sys_vals)
            f["bp_systolic_max"] = max(sys_vals)
            f["bp_readings_count"] = len(sys_vals)
            if len(sys_vals) >= 3:
                mid = len(sys_vals) // 2
                recent = sum(sys_vals[:mid]) / mid
                older = sum(sys_vals[mid:]) / (len(sys_vals) - mid)
                diff = recent - older
                f["bp_trend"] = "rising" if diff > 3 else ("improving" if diff < -3 else "steady")
                f["bp_trend_velocity"] = round(diff, 1)
            else:
                f["bp_trend"] = "just_started"
                f["bp_trend_velocity"] = 0
        if dia_vals:
            f["bp_diastolic_avg"] = round(sum(dia_vals) / len(dia_vals), 1)
            f["bp_diastolic_latest"] = dia_vals[0]

    if not f["has_bp_data"]:
        f["bp_systolic_avg"] = None
        f["bp_diastolic_avg"] = None
        f["bp_readings_count"] = 0
        f["bp_trend"] = None

    # Blood Sugar
    f["has_sugar_data"] = False
    if sugar_readings:
        sg_vals = [r.fasting_glucose for r in sugar_readings if r.fasting_glucose]
        if sg_vals:
            f["has_sugar_data"] = True
            f["sugar_avg"] = round(sum(sg_vals) / len(sg_vals), 1)
            f["sugar_latest"] = sg_vals[0]
            f["sugar_min"] = min(sg_vals)
            f["sugar_max"] = max(sg_vals)
            f["sugar_readings_count"] = len(sg_vals)
            f["sugar_above_100_count"] = sum(1 for v in sg_vals if v > 100)
            if len(sg_vals) >= 3:
                mid = len(sg_vals) // 2
                recent = sum(sg_vals[:mid]) / mid
                older = sum(sg_vals[mid:]) / (len(sg_vals) - mid)
                diff = recent - older
                f["sugar_trend"] = "rising" if diff > 5 else ("improving" if diff < -5 else "steady")
            else:
                f["sugar_trend"] = "just_started"

    if not f["has_sugar_data"]:
        f["sugar_avg"] = None
        f["sugar_readings_count"] = 0
        f["sugar_trend"] = None

    # Blood Report — ALL markers
    f["has_report"] = False
    if report:
        f["has_report"] = True
        # CBC RBC
        f["hemoglobin"] = float(report.hemoglobin) if report.hemoglobin else None
        f["rbc_count"] = float(report.rbc_count) if report.rbc_count else None
        f["pcv"] = float(report.pcv) if report.pcv else None
        f["mcv"] = float(report.mcv) if report.mcv else None
        f["mch"] = float(report.mch) if report.mch else None
        f["mchc"] = float(report.mchc) if report.mchc else None
        f["rdw"] = float(report.rdw) if report.rdw else None
        f["mpv"] = float(report.mpv) if report.mpv else None
        # CBC WBC
        f["wbc_count"] = float(report.wbc_count) if report.wbc_count else None
        f["neutrophils_pct"] = float(report.neutrophils_pct) if report.neutrophils_pct else None
        f["lymphocytes_pct"] = float(report.lymphocytes_pct) if report.lymphocytes_pct else None
        f["eosinophils_pct"] = float(report.eosinophils_pct) if report.eosinophils_pct else None
        f["monocytes_pct"] = float(report.monocytes_pct) if report.monocytes_pct else None
        # Platelets
        f["platelet_count"] = float(report.platelet_count) if report.platelet_count else None
        # Sugar from report
        f["fasting_glucose_report"] = float(report.fasting_glucose) if report.fasting_glucose else None
        f["random_glucose_report"] = float(report.random_glucose) if report.random_glucose else None
        f["hba1c"] = float(report.hba1c) if report.hba1c else None
        # Kidney
        f["creatinine"] = float(report.creatinine) if report.creatinine else None
        f["urea"] = float(report.urea) if report.urea else None
        f["uric_acid"] = float(report.uric_acid) if report.uric_acid else None
        f["egfr"] = float(report.egfr) if report.egfr else None
        # Liver
        f["sgpt"] = float(report.sgpt) if report.sgpt else None
        f["sgot"] = float(report.sgot) if report.sgot else None
        f["bilirubin_total"] = float(report.bilirubin_total) if report.bilirubin_total else None
        f["alkaline_phosphatase"] = float(report.alkaline_phosphatase) if report.alkaline_phosphatase else None
        f["albumin"] = float(report.albumin) if report.albumin else None
        # Lipids
        f["total_cholesterol"] = float(report.total_cholesterol) if report.total_cholesterol else None
        f["hdl"] = float(report.hdl) if report.hdl else None
        f["ldl"] = float(report.ldl) if report.ldl else None
        f["triglycerides"] = float(report.triglycerides) if report.triglycerides else None
        # Thyroid
        f["tsh"] = float(report.tsh) if report.tsh else None
        # Vitamins
        f["vitamin_d"] = float(report.vitamin_d) if report.vitamin_d else None
        f["vitamin_b12"] = float(report.vitamin_b12) if report.vitamin_b12 else None
        f["ferritin"] = float(report.ferritin) if report.ferritin else None
        f["iron"] = float(report.iron) if report.iron else None
        # Electrolytes
        f["sodium"] = float(report.sodium) if report.sodium else None
        f["potassium"] = float(report.potassium) if report.potassium else None
        f["calcium"] = float(report.calcium) if report.calcium else None
        # Peripheral smear
        f["peripheral_smear"] = report.peripheral_smear or None
    else:
        for key in ["hemoglobin", "platelet_count", "wbc_count", "fasting_glucose_report",
                    "random_glucose_report", "hba1c", "creatinine", "urea", "uric_acid",
                    "egfr", "sgpt", "sgot", "bilirubin_total", "total_cholesterol",
                    "hdl", "ldl", "triglycerides", "tsh", "vitamin_d", "vitamin_b12",
                    "ferritin", "iron", "sodium", "potassium", "calcium", "pcv",
                    "mcv", "rdw", "neutrophils_pct", "eosinophils_pct", "peripheral_smear"]:
            f[key] = None

    f["has_vitals_data"] = f["has_bp_data"] or f["has_sugar_data"] or f["has_report"]
    return f


# ════════════════════════════════════════════════════════════════
# 3. HEALTH INDEX
# ════════════════════════════════════════════════════════════════

def calculate_health_index(features: dict) -> int:
    if not features.get("has_vitals_data"):
        return 0

    score = 100.0

    # BP — use latest reading for immediate feedback
    bp_val = features.get("bp_systolic_latest") or features.get("bp_systolic_avg")
    if bp_val is not None:
        if bp_val < 120:      pass          # optimal
        elif bp_val < 130:    score -= 8    # elevated
        elif bp_val < 140:    score -= 18   # stage 1
        elif bp_val < 160:    score -= 28   # stage 2
        else:                 score -= 35   # crisis
        if features.get("bp_trend") == "rising":
            score -= 5

    # Sugar
    sugar_val = features.get("sugar_latest") or features.get("sugar_avg")
    if sugar_val is not None:
        if sugar_val < 100:   pass
        elif sugar_val < 126: score -= 12
        elif sugar_val < 200: score -= 25
        else:                 score -= 35
        if features.get("sugar_trend") == "rising":
            score -= 5

    # BMI
    bmi = features.get("bmi")
    if bmi is not None:
        if 18.5 <= bmi <= 24.9: pass
        elif 25 <= bmi <= 29.9: score -= 8
        elif bmi >= 30:         score -= 15
        elif bmi < 18.5:        score -= 10

    # Hemoglobin
    hb = features.get("hemoglobin")
    if hb is not None:
        hb_low = 13.5 if features.get("gender_enc") == 1 else 12.0
        if hb < hb_low - 2:  score -= 12
        elif hb < hb_low:    score -= 6

    # Platelets
    platelets = features.get("platelet_count")
    if platelets is not None:
        if platelets < 100000:   score -= 15
        elif platelets < 150000: score -= 8

    # Liver (SGPT)
    sgpt = features.get("sgpt")
    if sgpt is not None:
        if sgpt > 80:    score -= 10
        elif sgpt > 45:  score -= 5

    # Cholesterol
    ldl = features.get("ldl")
    if ldl is not None:
        if ldl > 160:    score -= 10
        elif ldl > 130:  score -= 5

    # Thyroid
    tsh = features.get("tsh")
    if tsh is not None:
        if tsh > 10 or tsh < 0.3:  score -= 8
        elif tsh > 5 or tsh < 0.5: score -= 4

    # Vitamin D
    vit_d = features.get("vitamin_d")
    if vit_d is not None:
        if vit_d < 10:   score -= 8
        elif vit_d < 20: score -= 4

    # Vitamin B12
    vit_b12 = features.get("vitamin_b12")
    if vit_b12 is not None:
        if vit_b12 < 150:  score -= 8
        elif vit_b12 < 200: score -= 4

    # Lifestyle
    if features.get("smoking"):                    score -= 8
    if features.get("alcohol"):                    score -= 5
    if features.get("stress_level", 5) >= 8:       score -= 5
    if features.get("activity_level", 3) <= 1:     score -= 5
    if features.get("family_hx_diabetes"):         score -= 3
    if features.get("family_hx_heart"):            score -= 3

    return max(10, min(100, round(score)))


# ════════════════════════════════════════════════════════════════
# 4. FUTURE PREVENTIVE CARE — What WILL happen if not addressed
#    NOT current status — FUTURE risk predictions with timeline
# ════════════════════════════════════════════════════════════════

def generate_preventive_care(features: dict) -> list[dict]:
    """
    Each item tells the user:
    - What their current data suggests about their FUTURE health
    - What specific risk they face in 6 months / 1 year / 5 years
    - What they can do NOW to prevent that future outcome
    """
    care_items = []
    if not features.get("has_vitals_data"):
        return care_items

    age = features.get("age") or 35
    gender = features.get("gender", "male")
    smoking = features.get("smoking", False)
    family_hx_heart = features.get("family_hx_heart", False)
    family_hx_diabetes = features.get("family_hx_diabetes", False)
    bmi = features.get("bmi")

    # ── BLOOD PRESSURE — Future Risk ──
    bp_val = features.get("bp_systolic_latest") or features.get("bp_systolic_avg")
    bp_trend = features.get("bp_trend", "steady")
    if bp_val is not None:
        if bp_val < 120:
            # Normal BP — predict what keeps it good
            future_risk = (
                f"Your BP is in the ideal range today. "
                f"At your current trajectory, you have a {'high' if (smoking or family_hx_heart) else 'low'} "
                f"risk of developing hypertension in the next 5 years. "
                f"{'Family history of heart disease increases this risk — stay proactive.' if family_hx_heart else 'Keep this up and your heart health at 60 will thank you.'}"
            )
            steps = [
                "Continue daily 30-min walks — this is your #1 protection",
                "Keep sodium under 2g/day to maintain this range",
                "Annual BP check is enough at this level",
            ]
            if smoking:
                steps.insert(0, "Quitting smoking will cut your future heart risk by 50%")
            care_items.append({
                "category": "blood_pressure",
                "urgency": "great",
                "current_status": f"BP {bp_val:.0f} mmHg — Ideal ✅",
                "future_risk_message": future_risk,
                "prevention_steps": steps,
                "risk_horizon": "5-year outlook: Low risk if habits maintained"
            })
        elif bp_val < 130:
            trend_note = " and it's been rising" if bp_trend == "rising" else ""
            future_risk = (
                f"Your BP is slightly elevated at {bp_val:.0f} mmHg{trend_note}. "
                f"If this continues without change, there is a 40-60% chance of developing "
                f"Stage 1 hypertension within 12-18 months. "
                f"The good news — at this stage, lifestyle changes alone can fully reverse this. "
                f"People who act now avoid medication 80% of the time."
            )
            care_items.append({
                "category": "blood_pressure",
                "urgency": "watch",
                "current_status": f"BP {bp_val:.0f} mmHg — Slightly elevated",
                "future_risk_message": future_risk,
                "prevention_steps": [
                    "30-min brisk walk daily can drop BP by 5-8 mmHg in 4 weeks",
                    "Reduce salt — swap to lemon and herbs",
                    "Check BP again in 2 weeks to see your progress",
                    "Stress management: 10 min of deep breathing daily",
                ],
                "risk_horizon": "12-18 months to Stage 1 hypertension if unchanged"
            })
        elif bp_val < 140:
            future_risk = (
                f"At {bp_val:.0f} mmHg, you are in Stage 1 hypertension. "
                f"Without intervention, this level doubles your risk of stroke and heart attack "
                f"over the next 5 years. "
                f"The encouraging part — consistent walking and diet changes can bring this "
                f"to normal range within 8-12 weeks, often without medication."
            )
            care_items.append({
                "category": "blood_pressure",
                "urgency": "focus",
                "current_status": f"BP {bp_val:.0f} mmHg — Stage 1 Hypertension",
                "future_risk_message": future_risk,
                "prevention_steps": [
                    "Daily 30-min brisk walk is as effective as one BP tablet",
                    "DASH diet: more fruits, vegetables, less salt",
                    "Recheck BP every week — track your improvement",
                    "Doctor consultation recommended within 4 weeks",
                ],
                "risk_horizon": "5-year stroke risk: 2x higher if untreated"
            })
        else:
            future_risk = (
                f"BP at {bp_val:.0f} mmHg is Stage 2 hypertension. "
                f"At this level, the risk of stroke in the next 3 years is significantly elevated. "
                f"Kidney damage and heart enlargement can begin silently within 1-2 years. "
                f"A doctor visit this week will give you a clear plan — "
                f"most people at this stage see dramatic improvement within 30 days of treatment."
            )
            care_items.append({
                "category": "blood_pressure",
                "urgency": "act_now",
                "current_status": f"BP {bp_val:.0f} mmHg — Stage 2 Hypertension",
                "future_risk_message": future_risk,
                "prevention_steps": [
                    "See a doctor this week — do not delay",
                    "Daily walking is your strongest natural tool alongside medication",
                    "Eliminate pickles, papad, and packaged food immediately",
                    "Check BP daily and log it here",
                ],
                "risk_horizon": "3-year stroke risk: Significantly elevated"
            })

    # ── BLOOD SUGAR — Future Risk ──
    sugar_val = features.get("sugar_latest") or features.get("sugar_avg")
    sugar_trend = features.get("sugar_trend", "steady")
    if sugar_val is not None:
        if sugar_val < 100:
            future_risk = (
                f"Your fasting sugar is {sugar_val:.0f} mg/dL — perfectly normal. "
                f"{'With family history of diabetes, your lifetime risk is 2-3x higher than average. ' if family_hx_diabetes else ''}"
                f"Maintaining this level now prevents Type 2 diabetes for decades. "
                f"People with consistently normal sugar at your age have a 70% lower lifetime diabetes risk."
            )
            care_items.append({
                "category": "blood_sugar",
                "urgency": "great",
                "current_status": f"Sugar {sugar_val:.0f} mg/dL — Normal ✅",
                "future_risk_message": future_risk,
                "prevention_steps": [
                    "Post-meal walks (even 10 min) keep insulin sensitivity high",
                    "Avoid sugary drinks — they spike sugar silently",
                    "Annual fasting sugar test is sufficient at this level",
                ],
                "risk_horizon": "Lifetime diabetes risk: Low if habits maintained"
            })
        elif sugar_val < 126:
            trend_note = " and trending upward" if sugar_trend == "rising" else ""
            future_risk = (
                f"Fasting sugar at {sugar_val:.0f} mg/dL{trend_note} is in the pre-diabetic range. "
                f"Without lifestyle changes, 15-30% of people at this level develop Type 2 diabetes "
                f"within 3-5 years. "
                f"The powerful news — the Diabetes Prevention Program showed that "
                f"walking 150 min/week and losing 5-7% body weight reduces this risk by 58%. "
                f"You have a real window to prevent this completely."
            )
            care_items.append({
                "category": "blood_sugar",
                "urgency": "watch",
                "current_status": f"Sugar {sugar_val:.0f} mg/dL — Pre-diabetic range",
                "future_risk_message": future_risk,
                "prevention_steps": [
                    "Walk 30 min after dinner — most effective sugar-lowering habit",
                    "Replace white rice with millets or brown rice",
                    "Recheck fasting sugar in 4 weeks to see your progress",
                    "HbA1c test gives you the 3-month average picture",
                ],
                "risk_horizon": "3-5 years to Type 2 diabetes if unchanged"
            })
        else:
            future_risk = (
                f"Fasting sugar at {sugar_val:.0f} mg/dL indicates diabetes. "
                f"Without treatment, this level causes nerve damage (neuropathy) within 5-7 years, "
                f"kidney damage within 10 years, and significantly increases heart disease risk. "
                f"The encouraging reality — with proper management, most people with diabetes "
                f"live full, healthy lives and can even achieve remission with lifestyle changes."
            )
            care_items.append({
                "category": "blood_sugar",
                "urgency": "focus",
                "current_status": f"Sugar {sugar_val:.0f} mg/dL — Diabetic range",
                "future_risk_message": future_risk,
                "prevention_steps": [
                    "HbA1c test immediately — gives your 3-month sugar average",
                    "Doctor consultation this week for a management plan",
                    "Daily 30-min walk is as powerful as metformin for early diabetes",
                    "Eliminate sugary drinks and fruit juices completely",
                ],
                "risk_horizon": "5-7 years to nerve damage if unmanaged"
            })

    # ── HEMOGLOBIN — Future Risk ──
    hb = features.get("hemoglobin")
    if hb is not None:
        hb_low = 13.5 if features.get("gender_enc") == 1 else 12.0
        if hb >= hb_low:
            care_items.append({
                "category": "hemoglobin",
                "urgency": "great",
                "current_status": f"Hemoglobin {hb} g/dL — Healthy ✅",
                "future_risk_message": (
                    f"Your hemoglobin is in the healthy range at {hb} g/dL. "
                    f"Good hemoglobin means your organs are getting optimal oxygen. "
                    f"Maintaining iron-rich foods in your diet will keep this stable for years. "
                    f"Women are at higher risk of iron deficiency after 40 — keep monitoring annually."
                ),
                "prevention_steps": [
                    "Continue iron-rich foods: spinach, dal, eggs, jaggery",
                    "Vitamin C with meals boosts iron absorption",
                    "Annual CBC check is sufficient",
                ],
                "risk_horizon": "Annual monitoring recommended"
            })
        elif hb >= hb_low - 1.5:
            care_items.append({
                "category": "hemoglobin",
                "urgency": "watch",
                "current_status": f"Hemoglobin {hb} g/dL — Mildly low",
                "future_risk_message": (
                    f"Hemoglobin at {hb} g/dL is mildly below normal. "
                    f"If this continues declining, you risk moderate anemia within 3-6 months — "
                    f"causing persistent fatigue, reduced immunity, and poor concentration. "
                    f"In pregnant women or those planning pregnancy, low hemoglobin significantly "
                    f"increases complications. The fix is straightforward: consistent iron-rich diet "
                    f"for 6-8 weeks typically restores levels completely."
                ),
                "prevention_steps": [
                    "Daily iron-rich meal: spinach dal, rajma, or eggs",
                    "Eat citrus fruit with iron foods — triples absorption",
                    "Avoid tea/coffee for 1 hour after meals",
                    "Retest CBC in 6-8 weeks to confirm improvement",
                ],
                "risk_horizon": "3-6 months to moderate anemia if diet unchanged"
            })
        else:
            care_items.append({
                "category": "hemoglobin",
                "urgency": "focus",
                "current_status": f"Hemoglobin {hb} g/dL — Significantly low",
                "future_risk_message": (
                    f"Hemoglobin at {hb} g/dL is significantly below normal. "
                    f"Without treatment, severe anemia can develop within 2-3 months, "
                    f"causing heart strain as it works harder to compensate for low oxygen. "
                    f"Long-term severe anemia increases heart failure risk. "
                    f"Iron supplementation under medical guidance can restore levels in 4-6 weeks."
                ),
                "prevention_steps": [
                    "Doctor visit this week — iron deficiency vs other causes needs diagnosis",
                    "Iron supplement (if prescribed) works in 4-6 weeks",
                    "Iron-rich foods every single day: spinach, lentils, jaggery, pomegranate",
                    "Avoid calcium supplements with iron — they compete for absorption",
                ],
                "risk_horizon": "2-3 months to severe anemia without treatment"
            })

    # ── PLATELETS — Future Risk ──
    platelets = features.get("platelet_count")
    if platelets is not None and platelets > 0:
        if platelets >= 150000:
            care_items.append({
                "category": "platelets",
                "urgency": "great",
                "current_status": f"Platelets {platelets:,}/cumm — Normal ✅",
                "future_risk_message": (
                    f"Your platelet count is healthy at {platelets:,}/cumm. "
                    f"Normal platelets mean your blood clots properly and your bone marrow is functioning well. "
                    f"Staying hydrated and avoiding alcohol keeps platelet production stable long-term."
                ),
                "prevention_steps": [
                    "Stay well hydrated — 8-10 glasses daily",
                    "Annual CBC check is sufficient",
                ],
                "risk_horizon": "Annual monitoring recommended"
            })
        elif platelets >= 100000:
            care_items.append({
                "category": "platelets",
                "urgency": "watch",
                "current_status": f"Platelets {platelets:,}/cumm — Mildly low",
                "future_risk_message": (
                    f"Platelets at {platelets:,}/cumm are mildly below the normal range of 150,000+. "
                    f"If this continues declining, you risk easy bruising and slower wound healing within months. "
                    f"Below 50,000 becomes a medical emergency. "
                    f"A retest in 2-3 weeks will confirm if this is temporary (common after viral illness) "
                    f"or a trend that needs medical attention."
                ),
                "prevention_steps": [
                    "Retest CBC in 2-3 weeks — this is the most important step",
                    "Eat fresh papaya daily — traditionally supports platelet production",
                    "Drink 10+ glasses of water daily",
                    "Avoid alcohol and NSAIDs (ibuprofen, aspirin) until retest",
                ],
                "risk_horizon": "2-3 weeks: retest to confirm trend"
            })
        else:
            care_items.append({
                "category": "platelets",
                "urgency": "act_now",
                "current_status": f"Platelets {platelets:,}/cumm — Critically low",
                "future_risk_message": (
                    f"Platelets at {platelets:,}/cumm is critically low. "
                    f"Below 100,000 significantly increases risk of spontaneous bleeding — "
                    f"including internal bleeding — within days to weeks without treatment. "
                    f"This requires immediate medical evaluation to identify the cause "
                    f"(dengue, ITP, bone marrow issue) and begin appropriate treatment."
                ),
                "prevention_steps": [
                    "See a doctor TODAY — do not delay",
                    "Avoid all blood-thinning medications (aspirin, ibuprofen)",
                    "Avoid contact sports or activities with injury risk",
                    "Papaya leaf extract — natural support while awaiting doctor",
                ],
                "risk_horizon": "Immediate medical attention required"
            })

    # ── BMI — Future Risk ──
    if bmi is not None:
        if features.get("bmi_class") == "overweight":
            future_risk = (
                f"BMI of {bmi} puts you in the overweight range. "
                f"Research shows that overweight individuals have a 2-3x higher risk of "
                f"developing Type 2 diabetes and hypertension within 10 years. "
                f"Losing just 5-7% of body weight (about {round((bmi - 24) * ((features.get('height_cm', 170)/100)**2), 1)} kg) "
                f"reduces diabetes risk by 58% and significantly lowers BP."
            )
            care_items.append({
                "category": "weight_bmi",
                "urgency": "watch",
                "current_status": f"BMI {bmi} — Overweight",
                "future_risk_message": future_risk,
                "prevention_steps": [
                    "30-min brisk walk daily — most sustainable weight loss tool",
                    "Smaller plates reduce calorie intake by 20% effortlessly",
                    "Replace sugary drinks with water or green tea",
                ],
                "risk_horizon": "10-year diabetes/hypertension risk: 2-3x higher"
            })
        elif features.get("bmi_class") == "obese":
            future_risk = (
                f"BMI of {bmi} is in the obese range. "
                f"At this level, the risk of Type 2 diabetes is 7x higher than normal weight. "
                f"Joint damage, sleep apnea, and fatty liver disease are likely within 5 years if unchanged. "
                f"The positive reality — even a 10% weight reduction dramatically reduces all these risks "
                f"and most people feel significantly better within 8-12 weeks of consistent effort."
            )
            care_items.append({
                "category": "weight_bmi",
                "urgency": "focus",
                "current_status": f"BMI {bmi} — Obese",
                "future_risk_message": future_risk,
                "prevention_steps": [
                    "Daily 30-min walk is your #1 priority",
                    "Consult a dietitian for a sustainable meal plan",
                    "Cut sugary snacks and drinks first — biggest impact",
                    "Sleep 7-8 hours — poor sleep drives weight gain",
                ],
                "risk_horizon": "5-year risk: Diabetes 7x, joint damage, fatty liver"
            })

    # ── CREATININE — Future Kidney Risk ──
    creatinine = features.get("creatinine")
    if creatinine is not None and creatinine > 1.2:
        care_items.append({
            "category": "kidney_health",
            "urgency": "watch",
            "current_status": f"Creatinine {creatinine} mg/dL — Slightly elevated",
            "future_risk_message": (
                f"Creatinine at {creatinine} mg/dL is slightly above normal (0.7-1.2). "
                f"If this trend continues, kidney function may decline by 10-15% per year, "
                f"potentially leading to chronic kidney disease within 5-10 years. "
                f"Staying well hydrated and reducing protein-heavy meals can stabilize this. "
                f"A follow-up test in 3 months will show if this is a trend or a one-time reading."
            ),
            "prevention_steps": [
                "Drink 10+ glasses of water daily — kidneys need hydration",
                "Reduce red meat and heavy protein meals",
                "Avoid NSAIDs (ibuprofen) — they stress kidneys",
                "Follow-up creatinine test in 3 months",
            ],
            "risk_horizon": "5-10 years to CKD if trend continues"
        })

    # Post-process: add risk scores
    for item in care_items:
        cat = item["category"]
        if cat == "blood_pressure":
            val = features.get("bp_systolic_latest") or features.get("bp_systolic_avg", 120)
            item["risk_score"] = min(95, max(10, int((val - 90) / 0.8)))
        elif cat == "blood_sugar":
            val = features.get("sugar_latest") or features.get("sugar_avg", 90)
            item["risk_score"] = min(95, max(10, int((val - 60) / 1.5))) if val else 30
        elif cat == "hemoglobin":
            hb_v = features.get("hemoglobin")
            hb_low = 13.5 if features.get("gender_enc") == 1 else 12.0
            item["risk_score"] = min(90, max(10, int(100 - (hb_v / hb_low) * 80))) if hb_v else 30
        elif cat == "platelets":
            p = features.get("platelet_count", 200000)
            item["risk_score"] = min(95, max(10, int(100 - (p / 200000) * 70))) if p else 30
        elif cat == "weight_bmi":
            b = features.get("bmi", 25)
            item["risk_score"] = min(85, max(10, int((b - 18) * 5))) if b else 30
        else:
            item["risk_score"] = 30
        steps = item.get("prevention_steps", [])
        item["top_action"] = steps[0] if steps else "Monitor regularly"

    return care_items


# ════════════════════════════════════════════════════════════════
# 5. DAILY TASKS — Present actions based on current data
# ════════════════════════════════════════════════════════════════

def _get_step_target(features: dict) -> tuple[int, int, str]:
    base_steps = 5000
    coins = 15
    bp_val = features.get("bp_systolic_latest") or features.get("bp_systolic_avg")
    if bp_val:
        if bp_val >= 140:    base_steps = max(base_steps, 10000); coins = 25
        elif bp_val >= 130:  base_steps = max(base_steps, 8000);  coins = 20
        elif bp_val >= 120:  base_steps = max(base_steps, 7000);  coins = 18
    sugar_val = features.get("sugar_latest") or features.get("sugar_avg")
    if sugar_val and sugar_val >= 100:
        base_steps = max(base_steps, 8000); coins = max(coins, 20)
    bmi = features.get("bmi")
    if bmi:
        if bmi >= 30:    base_steps = max(base_steps, 10000); coins = max(coins, 25)
        elif bmi >= 27:  base_steps = max(base_steps, 8000);  coins = max(coins, 20)
    hb = features.get("hemoglobin")
    if hb and hb < 11.0:
        base_steps = min(base_steps, 5000); coins = min(coins, 15)
    report_glucose = features.get("fasting_glucose_report")
    if report_glucose:
        if report_glucose >= 126:   base_steps = max(base_steps, 10000); coins = max(coins, 25)
        elif report_glucose >= 100: base_steps = max(base_steps, 7000);  coins = max(coins, 18)
    minutes = base_steps // 400
    return (base_steps, coins, f"{minutes} min / {base_steps:,} steps")


def generate_daily_tasks(features: dict, user) -> list[dict]:
    tasks = []
    if not features.get("has_vitals_data"):
        return tasks

    bp_val = features.get("bp_systolic_latest") or features.get("bp_systolic_avg")
    sugar_val = features.get("sugar_latest") or features.get("sugar_avg")
    bmi = features.get("bmi")
    hb = features.get("hemoglobin")
    platelets = features.get("platelet_count")
    report_glucose = features.get("fasting_glucose_report")

    # Walking task (always, coins based on health data)
    steps, walk_coins, duration = _get_step_target(features)
    why_parts = []
    if bp_val and bp_val >= 120:    why_parts.append(f"BP {bp_val:.0f} mmHg")
    if sugar_val and sugar_val >= 100: why_parts.append(f"Sugar {sugar_val:.0f} mg/dL")
    if bmi and bmi >= 25:           why_parts.append(f"BMI {bmi:.1f}")
    if report_glucose and report_glucose >= 100 and not sugar_val:
        why_parts.append(f"Report glucose {report_glucose:.0f}")
    why_msg = (f"Based on {', '.join(why_parts)} — " if why_parts else "") + f"{steps:,} steps helps naturally improve your numbers"
    tasks.append({
        "task_type": "MORNING_WALK",
        "task_name": f"Walk {steps:,} steps today",
        "description": "Your personalized step goal based on your health data",
        "why_this_task": why_msg,
        "category": "exercise",
        "time_of_day": "morning",
        "duration_or_quantity": duration,
        "coins_reward": walk_coins
    })

    # BP monitoring task
    if features.get("has_bp_data") and bp_val and bp_val >= 120:
        tasks.append({
            "task_type": "CHECK_BP_7DAYS",
            "task_name": "Log your BP this week",
            "description": "Track your blood pressure to see if lifestyle changes are working",
            "why_this_task": f"BP at {bp_val:.0f} mmHg — regular monitoring shows your progress",
            "category": "monitoring",
            "time_of_day": "morning",
            "duration_or_quantity": "1 BP reading",
            "coins_reward": 20
        })

    # Sugar monitoring task
    if features.get("has_sugar_data") and sugar_val and sugar_val >= 100:
        tasks.append({
            "task_type": "CHECK_SUGAR_7DAYS",
            "task_name": "Log fasting sugar this week",
            "description": "Track your glucose to see if diet changes are working",
            "why_this_task": f"Sugar at {sugar_val:.0f} mg/dL — weekly monitoring shows trends",
            "category": "monitoring",
            "time_of_day": "morning",
            "duration_or_quantity": "1 fasting glucose reading",
            "coins_reward": 20
        })
    elif features.get("has_report") and report_glucose and report_glucose >= 100:
        tasks.append({
            "task_type": "CHECK_SUGAR_7DAYS",
            "task_name": "Log fasting sugar this week",
            "description": "Your report shows elevated glucose — log a reading to monitor it",
            "why_this_task": f"Report glucose {report_glucose:.0f} mg/dL — weekly monitoring helps early detection",
            "category": "monitoring",
            "time_of_day": "morning",
            "duration_or_quantity": "1 fasting glucose reading",
            "coins_reward": 20
        })

    # BP diet guidance (0 coins)
    if features.get("has_bp_data") and bp_val and bp_val >= 130:
        tasks.append({
            "task_type": "LOW_SALT_MEAL",
            "task_name": "Go low-salt today",
            "description": "Use lemon and herbs instead of extra salt",
            "why_this_task": f"BP at {bp_val:.0f} — cutting sodium helps control blood pressure naturally",
            "category": "diet",
            "time_of_day": "all_day",
            "duration_or_quantity": "All meals today",
            "coins_reward": 0
        })

    # Sugar diet guidance (0 coins)
    if features.get("has_sugar_data") and sugar_val and sugar_val >= 100:
        tasks.append({
            "task_type": "NO_SUGAR_DAY",
            "task_name": "Skip added sugar today",
            "description": "No sugar in tea, coffee, or snacks",
            "why_this_task": f"Fasting glucose at {sugar_val:.0f} — reducing added sugar can lower it by 8-12 mg/dL",
            "category": "diet",
            "time_of_day": "all_day",
            "duration_or_quantity": "All day",
            "coins_reward": 0
        })

    # Hemoglobin task (0 coins)
    if features.get("has_report") and hb is not None:
        hb_low = 13.5 if features.get("gender_enc") == 1 else 12.0
        if hb < hb_low:
            tasks.append({
                "task_type": "IRON_RICH_MEAL",
                "task_name": "Eat iron-rich food today",
                "description": "Spinach dal, dates, pomegranate, or eggs",
                "why_this_task": f"Hemoglobin at {hb} g/dL — daily iron-rich food boosts it in 6 weeks",
                "category": "diet",
                "time_of_day": "lunch",
                "duration_or_quantity": "At least 1 iron-rich meal",
                "coins_reward": 0
            })

    # Platelet task (0 coins)
    if features.get("has_report") and platelets is not None and 0 < platelets < 150000:
        tasks.append({
            "task_type": "EAT_PAPAYA",
            "task_name": "Eat fresh papaya today",
            "description": "Papaya supports natural platelet production",
            "why_this_task": f"Platelets at {platelets:,} — papaya is traditionally linked to platelet recovery",
            "category": "diet",
            "time_of_day": "afternoon",
            "duration_or_quantity": "1 bowl fresh papaya",
            "coins_reward": 0
        })

    # BMI guidance (0 coins)
    if bmi is not None and bmi > 27:
        tasks.append({
            "task_type": "PORTION_CONTROL",
            "task_name": "Reduce portions by 20% today",
            "description": "Use a slightly smaller plate — you won't miss it",
            "why_this_task": f"BMI is {bmi} — small portion reduction leads to sustainable weight loss",
            "category": "diet",
            "time_of_day": "all_day",
            "duration_or_quantity": "All meals",
            "coins_reward": 0
        })

    # Hydration (coins — monitorable)
    if tasks:
        hydration_glasses = 8
        if bp_val and bp_val >= 130:                                hydration_glasses = 10
        if platelets is not None and platelets < 150000:            hydration_glasses = 10
        tasks.append({
            "task_type": "WATER_INTAKE",
            "task_name": f"Drink {hydration_glasses} glasses of water",
            "description": "Stay hydrated through the day",
            "why_this_task": "Hydration supports BP, kidney function, and overall health",
            "category": "wellness",
            "time_of_day": "all_day",
            "duration_or_quantity": f"{hydration_glasses} glasses (250ml each)",
            "coins_reward": 10
        })

    # Stress breathing (0 coins)
    if features.get("stress_level", 5) >= 7 and tasks:
        tasks.append({
            "task_type": "DEEP_BREATHING",
            "task_name": "5-min deep breathing",
            "description": "Slow belly breathing — calms your nervous system",
            "why_this_task": f"Stress level {features.get('stress_level')}/10 — deep breathing lowers cortisol and BP",
            "category": "wellness",
            "time_of_day": "evening",
            "duration_or_quantity": "5 minutes",
            "coins_reward": 0
        })

    return tasks


# ════════════════════════════════════════════════════════════════
# 6. DIET PLAN
# ════════════════════════════════════════════════════════════════

def generate_diet_plan(features: dict) -> dict | None:
    if not features.get("has_vitals_data"):
        return None

    bmi = features.get("bmi")
    bp_avg = features.get("bp_systolic_avg")
    sugar_avg = features.get("sugar_avg")
    hb = features.get("hemoglobin")
    platelets = features.get("platelet_count")
    gender_enc = features.get("gender_enc", 1)
    hb_low = 13.5 if gender_enc == 1 else 12.0
    report_glucose = features.get("fasting_glucose_report")

    eat_more, reduce, avoid = [], [], []
    focus_parts, reason_parts = [], []
    hydration = 8

    if bp_avg is not None and bp_avg >= 120:
        focus_parts.append("heart_healthy")
        reason_parts.append(f"Supporting your BP ({bp_avg:.0f} mmHg)")
        eat_more.extend(["Banana — natural potassium counters sodium", "Spinach and leafy greens", "Garlic — natural BP support", "Oats — helps reduce BP over time"])
        reduce.extend(["Extra salt — try lemon and herbs instead", "Tea/coffee to 1-2 cups daily"])
        avoid.extend(["Pickles and papad", "Packaged chips and namkeen", "Instant noodles"])
        hydration = max(hydration, 10)

    if sugar_avg is not None and sugar_avg >= 100:
        focus_parts.append("sugar_smart")
        reason_parts.append(f"Helping your sugar levels ({sugar_avg:.0f} mg/dL)")
        eat_more.extend(["Brown rice or millets (ragi, jowar, bajra)", "Bitter gourd — natural sugar support", "Methi seeds — soak overnight, eat morning", "Nuts as snacks (almonds, walnuts)"])
        reduce.extend(["White rice to half a cup", "Only low-GI fruits (apple, guava)"])
        avoid.extend(["Sugar in tea/coffee", "Fruit juices (even fresh ones)", "Maida products"])

    if hb is not None and hb < hb_low:
        focus_parts.append("iron_boost")
        reason_parts.append(f"Building up your hemoglobin ({hb} g/dL)")
        eat_more.extend(["Spinach, palak, methi daily", "Rajma, chana, masoor dal", "Jaggery instead of sugar", "Pomegranate and beetroot"])
        reduce.extend(["Tea right after meals — blocks iron"])
        hydration = max(hydration, 9)

    if platelets is not None and 0 < platelets < 150000:
        focus_parts.append("platelet_support")
        reason_parts.append(f"Supporting platelet recovery ({platelets:,})")
        eat_more.extend(["Fresh papaya", "Pomegranate seeds and juice", "Pumpkin and pumpkin seeds"])
        avoid.extend(["Alcohol completely"])
        hydration = max(hydration, 10)

    if bmi is not None and bmi >= 27:
        focus_parts.append("weight_friendly")
        reason_parts.append(f"Supporting your weight goals (BMI {bmi})")
        eat_more.extend(["Protein-rich breakfast (eggs, paneer)", "Salad before each meal", "Green tea instead of milk tea"])
        reduce.extend(["Portion sizes by 20%", "Fried food to twice a week"])
        avoid.extend(["Late night snacking", "Sugary drinks"])

    if report_glucose and report_glucose >= 100 and not features.get("has_sugar_data"):
        focus_parts.append("sugar_smart")
        reason_parts.append(f"Report shows glucose at {report_glucose:.0f} mg/dL")
        eat_more.extend(["Whole grains and millets", "Nuts and seeds as snacks"])
        avoid.extend(["Refined sugar and sweets"])

    if not focus_parts:
        focus_parts.append("balanced_wellness")
        reason_parts.append("Maintaining your healthy vitals")
        eat_more.extend(["Seasonal vegetables with every meal", "2-3 fruits daily", "Whole grains instead of refined", "Lean protein with every meal"])
        reduce.extend(["Fried foods to twice a week", "Packaged food"])
        avoid.extend(["Sugary drinks", "Trans fats"])

    return {
        "focus_type": " + ".join(focus_parts),
        "reason": ". ".join(reason_parts),
        "eat_more": list(dict.fromkeys(eat_more)),
        "reduce": list(dict.fromkeys(reduce)),
        "avoid": list(dict.fromkeys(avoid)),
        "hydration_goal": hydration
    }


# ════════════════════════════════════════════════════════════════
# 7. PERSISTENCE
# ════════════════════════════════════════════════════════════════

async def save_preventive_care(user_id: str, care_items: list[dict], db: AsyncSession):
    await db.execute(delete(PreventiveCare).where(PreventiveCare.user_id == user_id))
    for item in care_items:
        db.add(PreventiveCare(
            user_id=user_id,
            category=item["category"],
            urgency=item["urgency"],
            current_value=item["current_status"],
            future_risk_message=item["future_risk_message"],
            prevention_steps=json.dumps(item["prevention_steps"]),
            risk_horizon=item["risk_horizon"]
        ))

async def replace_todays_tasks(user_id: str, task_list: list[dict], db: AsyncSession):
    result = await db.execute(
        select(DailyTask)
        .where(DailyTask.user_id == user_id)
        .where(DailyTask.task_date == datetime.date.today())
        .where(DailyTask.completed == True)
    )
    completed_types = {t.task_type for t in result.scalars().all()}
    await db.execute(
        delete(DailyTask)
        .where(DailyTask.user_id == user_id)
        .where(DailyTask.task_date == datetime.date.today())
        .where(DailyTask.completed == False)
    )
    for t in task_list:
        if t["task_type"] in completed_types:
            continue
        db.add(DailyTask(
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
        ))

async def save_diet(user_id: str, diet: dict | None, db: AsyncSession):
    await db.execute(delete(DietRecommendation).where(DietRecommendation.user_id == user_id))
    if diet is None:
        return
    db.add(DietRecommendation(
        user_id=user_id,
        focus_type=diet["focus_type"],
        reason=diet["reason"],
        eat_more=json.dumps(diet["eat_more"]),
        reduce=json.dumps(diet["reduce"]),
        avoid=json.dumps(diet["avoid"]),
        hydration_goal_glasses=diet["hydration_goal"]
    ))

async def update_analysis_status(user_id: str, db: AsyncSession):
    result = await db.execute(select(UserDataStatus).where(UserDataStatus.user_id == user_id))
    status = result.scalar_one_or_none()
    if status:
        status.last_analysis_at = datetime.datetime.utcnow()
        status.analysis_ready = True


# ════════════════════════════════════════════════════════════════
# 8. MAIN PIPELINE
# ════════════════════════════════════════════════════════════════

async def run_full_analysis(user_id: str, db: AsyncSession):
    user = await get_user(user_id, db)
    if not user:
        return None

    bp_readings = await get_bp_readings(user_id, db)
    sugar_readings = await get_sugar_readings(user_id, db)
    latest_report = await get_latest_report(user_id, db)

    features = build_features(user, bp_readings, sugar_readings, latest_report)
    health_index = calculate_health_index(features)
    preventive = generate_preventive_care(features)
    tasks = generate_daily_tasks(features, user)
    diet = generate_diet_plan(features)

    print(f"🔬 Analysis: health_index={health_index}, care={len(preventive)}, tasks={len(tasks)}, diet={diet.get('focus_type') if diet else 'None'}")

    await save_preventive_care(user_id, preventive, db)
    await replace_todays_tasks(user_id, tasks, db)
    await save_diet(user_id, diet, db)
    await update_analysis_status(user_id, db)
    await db.flush()

    return {
        "health_index": health_index,
        "preventive_care": preventive,
        "tasks": tasks,
        "diet": diet
    }
