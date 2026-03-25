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

    # If no manual sugar readings but report has glucose — use it for diet/tasks
    if not f["has_sugar_data"] and f["has_report"]:
        rg = f.get("fasting_glucose_report") or f.get("random_glucose_report")
        if rg:
            f["sugar_latest"] = rg
            f["sugar_avg"] = rg
            f["sugar_readings_count"] = 1
            f["sugar_trend"] = "just_started"
            # Don't set has_sugar_data=True — keep it False so we know it's from report

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
    Preventive care — short 2-line positive messages per health metric.
    Correct BP thresholds: <120 normal, 120-129 elevated, 130-139 stage1, >=140 stage2.
    """
    care_items = []
    if not features.get("has_vitals_data"):
        return care_items

    smoking = features.get("smoking", False)
    family_hx_heart = features.get("family_hx_heart", False)
    family_hx_diabetes = features.get("family_hx_diabetes", False)
    bmi = features.get("bmi")

    # ── BLOOD PRESSURE ──
    bp_sys = features.get("bp_systolic_latest") or features.get("bp_systolic_avg")
    bp_dia = features.get("bp_diastolic_latest") or features.get("bp_diastolic_avg")
    if bp_sys is not None:
        if bp_sys <= 120 and (bp_dia is None or bp_dia <= 80):
            care_items.append({
                "category": "blood_pressure",
                "urgency": "great",
                "current_status": f"BP {bp_sys:.0f}/{int(bp_dia or 0)} mmHg — Normal ✅",
                "future_risk_message": "Your blood pressure is in the ideal range. Keep up daily walks and a low-salt diet to maintain this.",
                "prevention_steps": ["Continue 30-min daily walks", "Keep sodium under 2g/day"],
                "risk_horizon": ""
            })
        elif bp_sys < 130:
            care_items.append({
                "category": "blood_pressure",
                "urgency": "watch",
                "current_status": f"BP {bp_sys:.0f}/{int(bp_dia or 0)} mmHg — Slightly elevated",
                "future_risk_message": "BP is mildly elevated. A 30-min daily walk and reducing salt can bring it back to normal in 4 weeks.",
                "prevention_steps": ["30-min brisk walk daily", "Reduce salt — use lemon and herbs instead"],
                "risk_horizon": ""
            })
        elif bp_sys < 140:
            care_items.append({
                "category": "blood_pressure",
                "urgency": "focus",
                "current_status": f"BP {bp_sys:.0f}/{int(bp_dia or 0)} mmHg — Stage 1 Hypertension",
                "future_risk_message": "Stage 1 hypertension detected. Consistent walking and DASH diet can normalize this in 8-12 weeks.",
                "prevention_steps": ["Daily 30-min brisk walk", "DASH diet: more fruits, less salt"],
                "risk_horizon": ""
            })
        else:
            care_items.append({
                "category": "blood_pressure",
                "urgency": "act_now",
                "current_status": f"BP {bp_sys:.0f}/{int(bp_dia or 0)} mmHg — Stage 2 Hypertension",
                "future_risk_message": "BP needs immediate attention. Please consult a doctor this week — most people see improvement within 30 days.",
                "prevention_steps": ["See a doctor this week", "Eliminate pickles, papad, and packaged food"],
                "risk_horizon": ""
            })

    # ── BLOOD SUGAR ──
    sugar_val = features.get("sugar_latest") or features.get("sugar_avg")
    sugar_trend = features.get("sugar_trend", "steady")
    if sugar_val is not None:
        if sugar_val < 100:
            msg = "Your blood sugar is perfectly normal. Post-meal walks keep insulin sensitivity high long-term."
            if family_hx_diabetes:
                msg = "Sugar is normal — great! With family history of diabetes, keep up walks and avoid sugary drinks."
            care_items.append({
                "category": "blood_sugar", "urgency": "great",
                "current_status": f"Sugar {sugar_val:.0f} mg/dL — Normal ✅",
                "future_risk_message": msg,
                "prevention_steps": ["10-min walk after meals", "Avoid sugary drinks"],
                "risk_horizon": ""
            })
        elif sugar_val < 126:
            care_items.append({
                "category": "blood_sugar", "urgency": "watch",
                "current_status": f"Sugar {sugar_val:.0f} mg/dL — Pre-diabetic range",
                "future_risk_message": "Sugar is in the pre-diabetic range. Walking 30 min after dinner and switching to millets can reverse this.",
                "prevention_steps": ["Walk 30 min after dinner", "Replace white rice with millets or brown rice"],
                "risk_horizon": ""
            })
        else:
            care_items.append({
                "category": "blood_sugar", "urgency": "focus",
                "current_status": f"Sugar {sugar_val:.0f} mg/dL — High",
                "future_risk_message": "Sugar levels are high. A doctor visit and daily 30-min walk are the two most impactful steps right now.",
                "prevention_steps": ["Doctor consultation this week", "Daily 30-min walk — as effective as early medication"],
                "risk_horizon": ""
            })

    # ── HEMOGLOBIN (from blood report) ──
    hb = features.get("hemoglobin")
    if hb is not None:
        hb_low = 13.5 if features.get("gender_enc") == 1 else 12.0
        if hb >= hb_low:
            care_items.append({
                "category": "hemoglobin", "urgency": "great",
                "current_status": f"Hemoglobin {hb} g/dL — Healthy ✅",
                "future_risk_message": "Hemoglobin is healthy — your blood is carrying oxygen well. Keep eating iron-rich foods regularly.",
                "prevention_steps": ["Iron-rich foods: spinach, dal, eggs", "Vitamin C with meals boosts absorption"],
                "risk_horizon": ""
            })
        elif hb >= hb_low - 1.5:
            care_items.append({
                "category": "hemoglobin", "urgency": "watch",
                "current_status": f"Hemoglobin {hb} g/dL — Mildly low",
                "future_risk_message": "Hemoglobin is slightly low. Daily iron-rich meals with citrus fruit can restore it in 6-8 weeks.",
                "prevention_steps": ["Daily iron-rich meal: spinach dal, rajma, or eggs", "Eat citrus with iron foods — triples absorption"],
                "risk_horizon": ""
            })
        else:
            care_items.append({
                "category": "hemoglobin", "urgency": "focus",
                "current_status": f"Hemoglobin {hb} g/dL — Low",
                "future_risk_message": "Hemoglobin is significantly low. Please see a doctor — iron supplements can restore levels in 4-6 weeks.",
                "prevention_steps": ["Doctor visit this week", "Iron-rich foods daily: spinach, lentils, pomegranate"],
                "risk_horizon": ""
            })

    # ── PLATELETS (from blood report) ──
    platelets = features.get("platelet_count")
    if platelets is not None and platelets > 0:
        if platelets >= 150000:
            care_items.append({
                "category": "platelets", "urgency": "great",
                "current_status": f"Platelets {platelets:,}/cumm — Normal ✅",
                "future_risk_message": "Platelet count is healthy. Stay hydrated and avoid alcohol to keep it stable.",
                "prevention_steps": ["Stay hydrated — 8-10 glasses daily", "Annual CBC check is sufficient"],
                "risk_horizon": ""
            })
        elif platelets >= 100000:
            care_items.append({
                "category": "platelets", "urgency": "watch",
                "current_status": f"Platelets {platelets:,}/cumm — Mildly low",
                "future_risk_message": "Platelets are slightly low. Eat fresh papaya daily and retest in 2-3 weeks to confirm the trend.",
                "prevention_steps": ["Eat fresh papaya daily", "Retest CBC in 2-3 weeks"],
                "risk_horizon": ""
            })
        else:
            care_items.append({
                "category": "platelets", "urgency": "act_now",
                "current_status": f"Platelets {platelets:,}/cumm — Critically low",
                "future_risk_message": "Platelet count is critically low. Please see a doctor today — avoid NSAIDs and contact sports.",
                "prevention_steps": ["See a doctor TODAY", "Avoid aspirin, ibuprofen, and contact sports"],
                "risk_horizon": ""
            })

    # ── BMI ──
    if bmi is not None:
        if features.get("bmi_class") == "overweight":
            care_items.append({
                "category": "weight_bmi", "urgency": "watch",
                "current_status": f"BMI {bmi} — Overweight",
                "future_risk_message": "BMI is in the overweight range. A 30-min daily walk and smaller portions can bring it to normal in 3 months.",
                "prevention_steps": ["30-min brisk walk daily", "Use a smaller plate — reduces intake by 20%"],
                "risk_horizon": ""
            })
        elif features.get("bmi_class") == "obese":
            care_items.append({
                "category": "weight_bmi", "urgency": "focus",
                "current_status": f"BMI {bmi} — Obese",
                "future_risk_message": "BMI needs attention. Even a 10% weight reduction significantly improves energy, BP, and sugar levels.",
                "prevention_steps": ["Daily 30-min walk is your #1 priority", "Cut sugary drinks and snacks first"],
                "risk_horizon": ""
            })

    # ── WBC COUNT (from blood report) — Immune system ──
    wbc = features.get("wbc_count")
    if wbc is not None:
        if wbc < 4000:
            care_items.append({
                "category": "immune_system", "urgency": "focus",
                "current_status": f"WBC {wbc:,.0f}/cumm — Low (Leukopenia)",
                "future_risk_message": f"Low WBC at {wbc:,.0f}/cumm weakens immunity. Consult a doctor — infections can become serious. Protein-rich diet helps.",
                "prevention_steps": ["See a doctor this week", "Protein-rich meals: eggs, dal, chicken", "Avoid crowded places — infection risk is high"],
                "risk_horizon": ""
            })
        elif wbc > 11000:
            care_items.append({
                "category": "immune_system", "urgency": "watch",
                "current_status": f"WBC {wbc:,.0f}/cumm — Elevated",
                "future_risk_message": f"Elevated WBC at {wbc:,.0f}/cumm may indicate infection or inflammation. Monitor for fever or pain — see a doctor if symptoms appear.",
                "prevention_steps": ["Monitor for fever, pain, or swelling", "Stay hydrated — 10+ glasses daily", "See doctor if symptoms persist beyond 3 days"],
                "risk_horizon": ""
            })

    # ── CREATININE (from blood report) ──
    creatinine = features.get("creatinine")
    if creatinine is not None and creatinine > 1.2:
        care_items.append({
            "category": "kidney_health", "urgency": "watch",
            "current_status": f"Creatinine {creatinine} mg/dL — Slightly elevated",
            "future_risk_message": "Creatinine is slightly above normal. Drink 10+ glasses of water daily and retest in 3 months.",
            "prevention_steps": ["Drink 10+ glasses of water daily", "Avoid ibuprofen — it stresses kidneys"],
            "risk_horizon": ""
        })

    # ── CHOLESTEROL (from blood report) ──
    ldl = features.get("ldl")
    total_chol = features.get("total_cholesterol")
    if ldl is not None and ldl > 130:
        urgency = "focus" if ldl > 160 else "watch"
        care_items.append({
            "category": "cholesterol", "urgency": urgency,
            "current_status": f"LDL {ldl:.0f} mg/dL — {'High' if ldl > 160 else 'Borderline high'}",
            "future_risk_message": f"LDL at {ldl:.0f} mg/dL increases heart disease risk over time. Oats, walnuts, and daily walks can lower it in 8 weeks.",
            "prevention_steps": ["Eat oats for breakfast daily — lowers LDL by 5-10%", "30-min brisk walk daily"],
            "risk_horizon": ""
        })
    elif total_chol is not None and total_chol > 200:
        care_items.append({
            "category": "cholesterol", "urgency": "watch",
            "current_status": f"Total Cholesterol {total_chol:.0f} mg/dL — Borderline",
            "future_risk_message": "Cholesterol is slightly elevated. Reducing fried food and adding oats can normalize it in 6-8 weeks.",
            "prevention_steps": ["Replace fried snacks with nuts", "Add oats or barley to daily diet"],
            "risk_horizon": ""
        })

    # ── LIVER / SGPT (from blood report) ──
    sgpt = features.get("sgpt")
    if sgpt is not None and sgpt > 45:
        urgency = "focus" if sgpt > 80 else "watch"
        care_items.append({
            "category": "liver_health", "urgency": urgency,
            "current_status": f"SGPT {sgpt:.0f} U/L — {'Elevated' if sgpt > 80 else 'Mildly elevated'}",
            "future_risk_message": f"SGPT at {sgpt:.0f} U/L suggests liver stress. Avoiding alcohol and fried food can normalize it in 4-6 weeks.",
            "prevention_steps": ["Avoid alcohol completely", "Turmeric milk daily — natural liver support"],
            "risk_horizon": ""
        })

    # ── VITAMIN D (from blood report) ──
    vit_d = features.get("vitamin_d")
    if vit_d is not None and vit_d < 20:
        urgency = "focus" if vit_d < 10 else "watch"
        care_items.append({
            "category": "vitamin_d", "urgency": urgency,
            "current_status": f"Vitamin D {vit_d:.0f} ng/mL — {'Deficient' if vit_d < 10 else 'Insufficient'}",
            "future_risk_message": f"Vitamin D at {vit_d:.0f} ng/mL affects bone strength and immunity. 15 min morning sunlight daily can help significantly.",
            "prevention_steps": ["15 min morning sunlight (before 10am)", "Eggs and fatty fish 3x per week"],
            "risk_horizon": ""
        })

    # ── VITAMIN B12 (from blood report) ──
    vit_b12 = features.get("vitamin_b12")
    if vit_b12 is not None and vit_b12 < 200:
        urgency = "focus" if vit_b12 < 150 else "watch"
        care_items.append({
            "category": "vitamin_b12", "urgency": urgency,
            "current_status": f"Vitamin B12 {vit_b12:.0f} pg/mL — {'Deficient' if vit_b12 < 150 else 'Low'}",
            "future_risk_message": f"B12 at {vit_b12:.0f} pg/mL can cause fatigue and nerve issues. Daily eggs or dairy and a doctor-advised supplement can restore it.",
            "prevention_steps": ["Eggs, paneer, or dairy every day", "Ask doctor about B12 supplement"],
            "risk_horizon": ""
        })

    # ── THYROID / TSH (from blood report) ──
    tsh = features.get("tsh")
    if tsh is not None:
        if tsh > 10:
            care_items.append({
                "category": "thyroid", "urgency": "focus",
                "current_status": f"TSH {tsh:.2f} mIU/L — Hypothyroidism",
                "future_risk_message": f"TSH at {tsh:.2f} mIU/L indicates underactive thyroid. This causes fatigue, weight gain, and depression. Doctor-prescribed medication normalizes it in 4-6 weeks.",
                "prevention_steps": ["See an endocrinologist this week", "Iodized salt in cooking", "Avoid raw cabbage and soy in excess"],
                "risk_horizon": ""
            })
        elif tsh > 5:
            care_items.append({
                "category": "thyroid", "urgency": "watch",
                "current_status": f"TSH {tsh:.2f} mIU/L — Borderline high",
                "future_risk_message": f"TSH at {tsh:.2f} mIU/L is borderline. Retest in 3 months — if it rises further, medication may be needed.",
                "prevention_steps": ["Retest TSH in 3 months", "Ensure iodized salt in diet", "Monitor for fatigue or unexplained weight gain"],
                "risk_horizon": ""
            })
        elif tsh < 0.3:
            care_items.append({
                "category": "thyroid", "urgency": "focus",
                "current_status": f"TSH {tsh:.2f} mIU/L — Hyperthyroidism",
                "future_risk_message": f"TSH at {tsh:.2f} mIU/L indicates overactive thyroid. This causes rapid heartbeat, anxiety, and weight loss. See a doctor immediately.",
                "prevention_steps": ["See an endocrinologist this week", "Avoid excess iodine (seaweed, iodine supplements)", "Monitor heart rate and anxiety levels"],
                "risk_horizon": ""
            })

    # ── UREA (from blood report) — Kidney function ──
    urea = features.get("urea")
    if urea is not None and urea > 40:
        care_items.append({
            "category": "kidney_health", "urgency": "watch",
            "current_status": f"Urea {urea:.1f} mg/dL — Elevated",
            "future_risk_message": f"Urea at {urea:.1f} mg/dL suggests kidney stress or dehydration. Drink 10+ glasses of water daily and retest in 2 weeks.",
            "prevention_steps": ["Drink 10+ glasses of water daily", "Reduce protein intake slightly", "Retest kidney function in 2 weeks"],
            "risk_horizon": ""
        })

    # ── TRIGLYCERIDES (from blood report) ──
    triglycerides = features.get("triglycerides")
    if triglycerides is not None and triglycerides > 150:
        urgency = "focus" if triglycerides > 200 else "watch"
        care_items.append({
            "category": "triglycerides", "urgency": urgency,
            "current_status": f"Triglycerides {triglycerides:.0f} mg/dL — {'High' if triglycerides > 200 else 'Borderline'}",
            "future_risk_message": f"Triglycerides at {triglycerides:.0f} mg/dL increase heart disease and pancreatitis risk. Cut sugar and alcohol — levels drop 30% in 8 weeks.",
            "prevention_steps": ["Eliminate sugar in tea/coffee", "Avoid alcohol completely", "30-min brisk walk daily"],
            "risk_horizon": ""
        })

    # ── HDL CHOLESTEROL (from blood report) — "Good" cholesterol ──
    hdl = features.get("hdl")
    if hdl is not None and hdl < 40:
        care_items.append({
            "category": "hdl_cholesterol", "urgency": "watch",
            "current_status": f"HDL {hdl:.0f} mg/dL — Low (protective cholesterol)",
            "future_risk_message": f"HDL at {hdl:.0f} mg/dL is too low — this is your 'good' cholesterol that protects your heart. Exercise and nuts raise it naturally.",
            "prevention_steps": ["30-min brisk walk 5 days/week", "Handful of walnuts or almonds daily", "Olive oil instead of ghee for cooking"],
            "risk_horizon": ""
        })

    # ── RBC INDICES — MCV (Mean Corpuscular Volume) for anemia type ──
    mcv = features.get("mcv")
    if mcv is not None and hb is not None and hb < hb_low:
        if mcv < 80:
            # Microcytic anemia — iron deficiency
            care_items.append({
                "category": "anemia_type", "urgency": "watch",
                "current_status": f"MCV {mcv:.1f} fL + Low Hb — Iron deficiency anemia",
                "future_risk_message": "Low MCV with low hemoglobin indicates iron deficiency. Daily iron-rich foods with vitamin C can restore levels in 6-8 weeks.",
                "prevention_steps": ["Iron-rich foods: spinach, rajma, eggs", "Eat citrus fruit with iron meals — triples absorption", "Avoid tea within 1 hour of meals"],
                "risk_horizon": ""
            })
        elif mcv > 100:
            # Macrocytic anemia — B12/folate deficiency
            care_items.append({
                "category": "anemia_type", "urgency": "watch",
                "current_status": f"MCV {mcv:.1f} fL + Low Hb — B12/Folate deficiency anemia",
                "future_risk_message": "High MCV with low hemoglobin suggests B12 or folate deficiency. Daily eggs/dairy and a B12 supplement can fix this in 4-6 weeks.",
                "prevention_steps": ["Eggs, paneer, or dairy every day", "Ask doctor about B12 supplement", "Folate-rich: spinach, lentils, chickpeas"],
                "risk_horizon": ""
            })

    # Post-process: risk scores + top_action
    for item in care_items:
        cat = item["category"]
        if cat == "blood_pressure":
            val = features.get("bp_systolic_latest") or features.get("bp_systolic_avg", 115)
            item["risk_score"] = min(95, max(5, int((val - 90) / 0.8)))
        elif cat == "blood_sugar":
            val = features.get("sugar_latest") or features.get("sugar_avg", 90)
            item["risk_score"] = min(95, max(5, int((val - 60) / 1.5))) if val else 20
        elif cat == "hemoglobin":
            hb_v = features.get("hemoglobin", 14)
            hb_low = 13.5 if features.get("gender_enc") == 1 else 12.0
            item["risk_score"] = min(90, max(5, int(100 - (hb_v / hb_low) * 80)))
        elif cat == "platelets":
            p = features.get("platelet_count", 200000)
            item["risk_score"] = min(95, max(5, int(100 - (p / 200000) * 70)))
        elif cat == "weight_bmi":
            b = features.get("bmi", 22)
            item["risk_score"] = min(85, max(5, int((b - 18) * 5)))
        elif cat == "cholesterol":
            ldl_v = features.get("ldl") or features.get("total_cholesterol", 180)
            item["risk_score"] = min(85, max(5, int((ldl_v - 100) / 1.2)))
        elif cat == "liver_health":
            sgpt_v = features.get("sgpt", 40)
            item["risk_score"] = min(85, max(5, int((sgpt_v - 20) / 0.8)))
        elif cat in ("vitamin_d", "vitamin_b12"):
            item["risk_score"] = 35
        elif cat == "immune_system":
            wbc_v = features.get("wbc_count", 7000)
            if wbc_v < 4000:
                item["risk_score"] = min(75, max(20, int((4000 - wbc_v) / 40)))
            else:
                item["risk_score"] = min(60, max(20, int((wbc_v - 11000) / 100)))
        elif cat == "thyroid":
            tsh_v = features.get("tsh", 2.5)
            if tsh_v > 5:
                item["risk_score"] = min(80, max(30, int((tsh_v - 5) * 8)))
            else:
                item["risk_score"] = min(80, max(30, int((0.5 - tsh_v) * 50)))
        elif cat == "triglycerides":
            trig_v = features.get("triglycerides", 150)
            item["risk_score"] = min(85, max(20, int((trig_v - 100) / 2)))
        elif cat == "hdl_cholesterol":
            hdl_v = features.get("hdl", 50)
            item["risk_score"] = min(70, max(20, int((50 - hdl_v) * 2)))
        elif cat == "anemia_type":
            item["risk_score"] = 45
        else:
            item["risk_score"] = 25
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
    # Use manual sugar OR report glucose
    sugar_val = features.get("sugar_latest") or features.get("sugar_avg")
    if not sugar_val:
        sugar_val = features.get("fasting_glucose_report") or features.get("random_glucose_report")
    bmi = features.get("bmi")
    hb = features.get("hemoglobin")
    platelets = features.get("platelet_count")
    report_glucose = features.get("fasting_glucose_report") or features.get("random_glucose_report")

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

    # WBC task (0 coins)
    wbc = features.get("wbc_count")
    if wbc is not None and wbc < 4000:
        tasks.append({
            "task_type": "PROTEIN_BOOST",
            "task_name": "Eat protein-rich meal today",
            "description": "Eggs, dal, or chicken — protein supports immune recovery",
            "why_this_task": f"WBC at {wbc:,.0f} — protein helps rebuild white blood cells",
            "category": "diet",
            "time_of_day": "lunch",
            "duration_or_quantity": "At least 1 protein-rich meal",
            "coins_reward": 0
        })

    # Thyroid task (0 coins)
    tsh = features.get("tsh")
    if tsh is not None and tsh > 5:
        tasks.append({
            "task_type": "IODIZED_SALT",
            "task_name": "Use iodized salt in cooking",
            "description": "Iodine supports thyroid function",
            "why_this_task": f"TSH at {tsh:.1f} mIU/L — iodine deficiency is common in India",
            "category": "diet",
            "time_of_day": "all_day",
            "duration_or_quantity": "All meals",
            "coins_reward": 0
        })

    # Triglycerides task (0 coins)
    triglycerides = features.get("triglycerides")
    if triglycerides is not None and triglycerides > 150:
        tasks.append({
            "task_type": "NO_SUGAR_NO_ALCOHOL",
            "task_name": "Skip sugar and alcohol today",
            "description": "Sugar and alcohol spike triglycerides",
            "why_this_task": f"Triglycerides at {triglycerides:.0f} mg/dL — cutting these drops levels by 30% in weeks",
            "category": "diet",
            "time_of_day": "all_day",
            "duration_or_quantity": "All day",
            "coins_reward": 0
        })

    # HDL task (0 coins)
    hdl = features.get("hdl")
    if hdl is not None and hdl < 40:
        tasks.append({
            "task_type": "NUTS_SNACK",
            "task_name": "Eat a handful of nuts today",
            "description": "Walnuts or almonds — raises good cholesterol naturally",
            "why_this_task": f"HDL at {hdl:.0f} mg/dL — nuts raise protective cholesterol",
            "category": "diet",
            "time_of_day": "afternoon",
            "duration_or_quantity": "1 handful (8-10 nuts)",
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
    # Use LATEST readings for diet — not averages — so diet reflects current state
    bp_latest = features.get("bp_systolic_latest") or features.get("bp_systolic_avg")
    sugar_latest = features.get("sugar_latest") or features.get("fasting_glucose_report") or features.get("random_glucose_report")
    hb = features.get("hemoglobin")
    platelets = features.get("platelet_count")
    gender_enc = features.get("gender_enc", 1)
    hb_low = 13.5 if gender_enc == 1 else 12.0
    # Additional report markers
    ldl = features.get("ldl")
    hdl = features.get("hdl")
    triglycerides = features.get("triglycerides")
    tsh = features.get("tsh")
    vit_d = features.get("vitamin_d")
    vit_b12 = features.get("vitamin_b12")
    creatinine = features.get("creatinine")
    urea = features.get("urea")
    sgpt = features.get("sgpt")
    wbc = features.get("wbc_count")
    mcv = features.get("mcv")

    eat_more, reduce, avoid = [], [], []
    focus_parts, reason_parts = [], []
    hydration = 8

    # Priority 1: Platelets (most urgent)
    if platelets is not None and 0 < platelets < 150000:
        focus_parts.append("platelet_support")
        reason_parts.append(f"Supporting platelet recovery ({int(platelets):,}/cumm)")
        eat_more.extend(["Fresh papaya daily", "Pomegranate seeds and juice", "Pumpkin and pumpkin seeds", "Lean protein: eggs, chicken, fish"])
        avoid.extend(["Alcohol completely", "Aspirin and ibuprofen without doctor advice"])
        hydration = max(hydration, 10)

    # Priority 2: Hemoglobin
    if hb is not None and hb < hb_low:
        focus_parts.append("iron_boost")
        reason_parts.append(f"Building up hemoglobin ({hb} g/dL)")
        eat_more.extend(["Spinach, palak, methi daily", "Rajma, chana, masoor dal", "Jaggery instead of sugar", "Pomegranate and beetroot", "Dates and raisins as snacks"])
        reduce.extend(["Tea right after meals — blocks iron absorption"])
        hydration = max(hydration, 9)

    # Priority 3: Blood Sugar (manual or from report)
    if sugar_latest is not None and sugar_latest >= 100:
        focus_parts.append("sugar_smart")
        reason_parts.append(f"Helping your sugar levels ({sugar_latest:.0f} mg/dL)")
        eat_more.extend(["Brown rice or millets (ragi, jowar, bajra)", "Bitter gourd — natural sugar support", "Methi seeds — soak overnight, eat morning", "Nuts as snacks (almonds, walnuts)"])
        reduce.extend(["White rice to half a cup", "Only low-GI fruits (apple, guava)"])
        avoid.extend(["Sugar in tea/coffee", "Fruit juices (even fresh ones)", "Maida products"])

    # Priority 4: Blood Pressure
    if bp_latest is not None and bp_latest >= 121:
        focus_parts.append("heart_healthy")
        reason_parts.append(f"Supporting your BP ({bp_latest:.0f} mmHg)")
        eat_more.extend(["Banana — natural potassium counters sodium", "Spinach and leafy greens", "Garlic — natural BP support", "Oats — helps reduce BP over time"])
        reduce.extend(["Extra salt — try lemon and herbs instead", "Tea/coffee to 1-2 cups daily"])
        avoid.extend(["Pickles and papad", "Packaged chips and namkeen", "Instant noodles"])
        hydration = max(hydration, 10)

    # Priority 5: Cholesterol (from report)
    if ldl is not None and ldl > 130:
        focus_parts.append("heart_healthy")
        reason_parts.append(f"Managing cholesterol (LDL {ldl:.0f} mg/dL)")
        eat_more.extend(["Oats and barley — lowers LDL naturally", "Walnuts and flaxseeds", "Olive oil instead of ghee for cooking"])
        avoid.extend(["Fried food and trans fats", "Full-fat dairy in excess"])

    # Priority 6: Liver (SGPT from report)
    if sgpt is not None and sgpt > 45:
        focus_parts.append("liver_support")
        reason_parts.append(f"Supporting liver health (SGPT {sgpt:.0f} U/L)")
        eat_more.extend(["Turmeric milk daily", "Amla (Indian gooseberry)", "Green tea"])
        avoid.extend(["Alcohol completely", "Fried and oily food", "Packaged processed food"])

    # Priority 7: Vitamin D deficiency (from report)
    if vit_d is not None and vit_d < 20:
        focus_parts.append("vitamin_boost")
        reason_parts.append(f"Boosting Vitamin D ({vit_d:.0f} ng/mL)")
        eat_more.extend(["Eggs (especially yolk)", "Fatty fish: salmon, sardines", "Fortified milk and cereals", "15 min morning sunlight daily"])

    # Priority 8: Vitamin B12 deficiency (from report)
    if vit_b12 is not None and vit_b12 < 200:
        if "vitamin_boost" not in focus_parts:
            focus_parts.append("vitamin_boost")
        reason_parts.append(f"Boosting Vitamin B12 ({vit_b12:.0f} pg/mL)")
        eat_more.extend(["Eggs, paneer, and dairy daily", "Chicken and fish if non-veg", "B12-fortified cereals"])

    # Priority 9: BMI
    if bmi is not None and bmi >= 27:
        focus_parts.append("weight_friendly")
        reason_parts.append(f"Supporting weight goals (BMI {bmi})")
        eat_more.extend(["Protein-rich breakfast (eggs, paneer)", "Salad before each meal", "Green tea instead of milk tea"])
        reduce.extend(["Portion sizes by 20%", "Fried food to twice a week"])
        avoid.extend(["Late night snacking", "Sugary drinks"])

    # Priority 10: Triglycerides (from report)
    if triglycerides is not None and triglycerides > 150:
        focus_parts.append("heart_healthy")
        reason_parts.append(f"Managing triglycerides ({triglycerides:.0f} mg/dL)")
        eat_more.extend(["Fatty fish: salmon, mackerel (omega-3)", "Flaxseeds and chia seeds"])
        avoid.extend(["Sugar in any form — biggest trigger", "Alcohol completely", "White bread and maida"])

    # Priority 11: Low HDL (from report)
    if hdl is not None and hdl < 40:
        focus_parts.append("heart_healthy")
        reason_parts.append(f"Raising good cholesterol (HDL {hdl:.0f} mg/dL)")
        eat_more.extend(["Walnuts and almonds daily", "Olive oil for cooking", "Fatty fish 2x per week"])

    # Priority 12: Thyroid (from report)
    if tsh is not None and tsh > 5:
        focus_parts.append("thyroid_support")
        reason_parts.append(f"Supporting thyroid function (TSH {tsh:.1f} mIU/L)")
        eat_more.extend(["Iodized salt in cooking", "Eggs and dairy", "Brazil nuts (selenium)"])
        avoid.extend(["Raw cabbage and broccoli in excess", "Soy products in large amounts"])

    # Priority 13: Low WBC (from report)
    if wbc is not None and wbc < 4000:
        focus_parts.append("immune_boost")
        reason_parts.append(f"Boosting immunity (WBC {wbc:,.0f}/cumm)")
        eat_more.extend(["Protein every meal: eggs, dal, chicken", "Citrus fruits daily", "Garlic and ginger in cooking"])
        avoid.extend(["Junk food and packaged snacks"])

    # Priority 14: Kidney stress (from report)
    if (creatinine is not None and creatinine > 1.2) or (urea is not None and urea > 40):
        focus_parts.append("kidney_friendly")
        reason_parts.append(f"Supporting kidney health")
        eat_more.extend(["10+ glasses of water daily", "Fresh fruits and vegetables"])
        reduce.extend(["Protein to moderate amounts", "Salt intake"])
        avoid.extend(["NSAIDs like ibuprofen without doctor advice"])
        hydration = max(hydration, 12)

    # Fallback: balanced
    if not focus_parts:
        focus_parts.append("balanced_wellness")
        reason_parts.append("Maintaining your healthy vitals")
        eat_more.extend(["Seasonal vegetables with every meal", "2-3 fruits daily", "Whole grains instead of refined", "Lean protein with every meal"])
        reduce.extend(["Fried foods to twice a week", "Packaged food"])
        avoid.extend(["Sugary drinks", "Trans fats"])

    return {
        "focus_type": " + ".join(focus_parts[:3]),  # Limit to 3 parts to stay under 50 chars
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
    await db.execute(delete(PreventiveCare).where(PreventiveCare.user_id == user_id).execution_options(synchronize_session="fetch"))
    await db.flush()
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
        .execution_options(synchronize_session="fetch")
    )
    await db.flush()
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
    await db.execute(delete(DietRecommendation).where(DietRecommendation.user_id == user_id).execution_options(synchronize_session="fetch"))
    await db.flush()
    if diet is None:
        return
    db.add(DietRecommendation(
        user_id=user_id,
        focus_type=diet["focus_type"],
        reason=diet["reason"],
        eat_more=json.dumps(diet["eat_more"]),
        reduce=json.dumps(diet["reduce"]),
        avoid=json.dumps(diet["avoid"]),
        hydration_goal_glasses=diet.get("hydration_goal_glasses") or diet.get("hydration_goal", 8)
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

    print(f"🔬 Analysis for {user_id}:")
    print(f"   BP={features.get('bp_systolic_latest')}, Sugar={features.get('sugar_latest')}, BMI={features.get('bmi')}")
    print(f"   Hb={features.get('hemoglobin')}, Platelets={features.get('platelet_count')}, has_report={features.get('has_report')}")
    print(f"   health_index={health_index}, care={len(preventive)}, tasks={len(tasks)}, diet={diet.get('focus_type') if diet else 'None'}")

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
