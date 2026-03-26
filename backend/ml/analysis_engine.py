"""
VitalID Analysis Engine V4 — FULL DATA FUSION + POSITIVE FRAMING
Considers ALL sources: BP, Sugar, BMI, Weight, Height, Blood Reports, Age, 
Lifestyle (smoking, alcohol, stress, activity), Family history.

DESIGN RULES:
1. Tasks ONLY generated when user has actual vitals data (BP or Sugar or Report)
2. All messaging uses POSITIVE FARMING — encouraging, not alarming
3. Every insight focuses on "what you CAN do" not "what's wrong"
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
        .order_by(desc(BPReading.measured_at))
        .limit(limit)
    )
    return row.scalars().all()

async def get_sugar_readings(user_id: str, db: AsyncSession, limit=30):
    row = await db.execute(
        select(SugarReading)
        .where(SugarReading.user_id == user_id)
        .order_by(desc(SugarReading.measured_at))
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
    
    # ── Anthropometrics ──
    f["weight_kg"] = float(user.weight_kg) if user.weight_kg else None
    f["height_cm"] = float(user.height_cm) if user.height_cm else None
    f["waist_cm"] = float(user.waist_cm) if user.waist_cm else None
    
    if f["weight_kg"] and f["height_cm"] and f["height_cm"] > 0:
        f["bmi"] = round(f["weight_kg"] / ((f["height_cm"] / 100) ** 2), 2)
    else:
        f["bmi"] = float(user.bmi) if user.bmi else None
    
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
    f["activity_level"] = user.activity_level or 1
    f["stress_level"] = user.stress_level or 5
    f["family_hx_diabetes"] = bool(user.family_hx_diabetes)
    f["family_hx_heart"] = bool(user.family_hx_heart)
    
    # ── Blood Pressure Analysis ──
    f["has_bp_data"] = False
    if bp_readings and len(bp_readings) > 0:
        sys_vals = [r.systolic for r in bp_readings if r.systolic]
        dia_vals = [r.diastolic for r in bp_readings if r.diastolic]
        
        if sys_vals:
            f["has_bp_data"] = True
            f["bp_systolic_avg"] = round(sum(sys_vals) / len(sys_vals), 1)
            f["bp_systolic_latest"] = sys_vals[0]
            f["bp_systolic_min"] = min(sys_vals)
            f["bp_systolic_max"] = max(sys_vals)
            f["bp_readings_count"] = len(sys_vals)

            # Days since last BP reading
            from datetime import date as _date
            latest_bp_date = bp_readings[0].measured_at.date() if hasattr(bp_readings[0].measured_at, 'date') else bp_readings[0].measured_at
            f["days_since_last_bp"] = (_date.today() - latest_bp_date).days
            
            if len(sys_vals) >= 4:
                mid = len(sys_vals) // 2
                recent = sum(sys_vals[:mid]) / mid
                older = sum(sys_vals[mid:]) / (len(sys_vals) - mid)
                diff = recent - older
                if diff > 3:
                    f["bp_trend"] = "rising"
                elif diff < -3:
                    f["bp_trend"] = "improving"
                else:
                    f["bp_trend"] = "steady"
                f["bp_trend_velocity"] = round(diff, 1)
            else:
                f["bp_trend"] = "just_started"
                f["bp_trend_velocity"] = 0
            
            f["bp_days_above_130"] = sum(1 for v in sys_vals if v >= 130)
        
        if dia_vals:
            f["bp_diastolic_avg"] = round(sum(dia_vals) / len(dia_vals), 1)
            f["bp_diastolic_latest"] = dia_vals[0]
    
    if not f["has_bp_data"]:
        f["bp_systolic_avg"] = None
        f["bp_diastolic_avg"] = None
        f["bp_readings_count"] = 0
        f["bp_trend"] = None
    
    # ── Blood Sugar Analysis ──
    f["has_sugar_data"] = False
    if sugar_readings and len(sugar_readings) > 0:
        sg_vals = [r.fasting_glucose for r in sugar_readings if r.fasting_glucose]
        
        if sg_vals:
            f["has_sugar_data"] = True
            f["sugar_avg"] = round(sum(sg_vals) / len(sg_vals), 1)
            f["sugar_latest"] = sg_vals[0]
            f["sugar_min"] = min(sg_vals)
            f["sugar_max"] = max(sg_vals)
            f["sugar_readings_count"] = len(sg_vals)
            f["sugar_above_100_count"] = sum(1 for v in sg_vals if v > 100)

            # Days since last sugar reading
            from datetime import date as _date
            latest_sugar_date = sugar_readings[0].measured_at.date() if hasattr(sugar_readings[0].measured_at, 'date') else sugar_readings[0].measured_at
            f["days_since_last_sugar"] = (_date.today() - latest_sugar_date).days
            
            if len(sg_vals) >= 4:
                mid = len(sg_vals) // 2
                recent = sum(sg_vals[:mid]) / mid
                older = sum(sg_vals[mid:]) / (len(sg_vals) - mid)
                diff = recent - older
                if diff > 5:
                    f["sugar_trend"] = "rising"
                elif diff < -5:
                    f["sugar_trend"] = "improving"
                else:
                    f["sugar_trend"] = "steady"
            else:
                f["sugar_trend"] = "just_started"
    
    if not f["has_sugar_data"]:
        f["sugar_avg"] = None
        f["sugar_readings_count"] = 0
        f["sugar_trend"] = None
    
    # ── Blood Report Values ──
    f["has_report"] = False
    if report:
        f["has_report"] = True
        # CBC
        f["hemoglobin"]           = float(report.hemoglobin) if report.hemoglobin else None
        f["rbc_count"]            = float(report.rbc_count) if report.rbc_count else None
        f["wbc_count"]            = int(report.wbc_count) if report.wbc_count else None
        f["platelet_count"]       = int(report.platelet_count) if report.platelet_count else None
        f["pcv"]                  = float(report.pcv) if report.pcv else None
        f["mchc"]                 = float(report.mchc) if report.mchc else None
        f["rdw"]                  = float(report.rdw) if report.rdw else None
        f["neutrophils_pct"]      = float(report.neutrophils_pct) if report.neutrophils_pct else None
        f["lymphocytes_pct"]      = float(report.lymphocytes_pct) if report.lymphocytes_pct else None
        f["peripheral_smear"]     = report.peripheral_smear or None
        # Biochemistry
        f["fasting_glucose_report"] = float(report.fasting_glucose) if report.fasting_glucose else None
        f["creatinine"]           = float(report.creatinine) if report.creatinine else None
        f["urea"]                 = float(report.urea) if report.urea else None
        f["sgpt"]                 = float(report.sgpt) if report.sgpt else None
        # Lipids
        f["total_cholesterol"]    = float(report.total_cholesterol) if report.total_cholesterol else None
        f["ldl"]                  = float(report.ldl) if report.ldl else None
        f["triglycerides"]        = float(report.triglycerides) if report.triglycerides else None
        f["hdl"]                  = float(report.hdl) if report.hdl else None
        # Thyroid
        f["tsh"]                  = float(report.tsh) if report.tsh else None
        # Vitamins
        f["vitamin_d"]            = float(report.vitamin_d) if report.vitamin_d else None
        f["vitamin_b12"]          = float(report.vitamin_b12) if report.vitamin_b12 else None
    else:
        f["hemoglobin"] = None
        f["platelet_count"] = None
        f["ldl"] = None
        f["triglycerides"] = None
        f["tsh"] = None
        f["creatinine"] = None
        f["sgpt"] = None
        f["vitamin_d"] = None
        f["vitamin_b12"] = None

    # ── Has ANY vitals data ──
    f["has_vitals_data"] = f["has_bp_data"] or f["has_sugar_data"] or f["has_report"]

    return f


# ════════════════════════════════════════════════════════════════
# 3. HEALTH INDEX CALCULATOR
# ════════════════════════════════════════════════════════════════

def calculate_health_index(features: dict) -> int:
    # ONLY calculate when user has actual vitals data
    if not features.get("has_vitals_data"):
        return 0
    
    score = 100.0
    
    # ── BP Score ──
    bp_avg = features.get("bp_systolic_latest", features.get("bp_systolic_avg"))
    if bp_avg is not None:
        if bp_avg < 120:
            pass
        elif bp_avg < 130:
            score -= 8
        elif bp_avg < 140:
            score -= 18
        elif bp_avg < 160:
            score -= 28
        else:
            score -= 35
        if features.get("bp_trend") == "rising":
            score -= 5
    
    # ── Sugar Score ──
    sugar_avg = features.get("sugar_latest", features.get("sugar_avg"))
    if sugar_avg is not None:
        if sugar_avg < 100:
            pass
        elif sugar_avg < 126:
            score -= 12
        elif sugar_avg < 200:
            score -= 25
        else:
            score -= 35
        if features.get("sugar_trend") == "rising":
            score -= 5
    
    # ── BMI Score ──
    bmi = features.get("bmi")
    if bmi is not None:
        if 18.5 <= bmi <= 24.9:
            pass
        elif 25 <= bmi <= 29.9:
            score -= 8
        elif bmi >= 30:
            score -= 15
        elif bmi < 18.5:
            score -= 10
    
    # ── Report Values ──
    hb = features.get("hemoglobin")
    if hb is not None:
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
    
    # ── Lifestyle ──
    if features.get("smoking"):
        score -= 8
    if features.get("alcohol"):
        score -= 5
    if features.get("stress_level", 5) >= 8:
        score -= 5
    if features.get("activity_level", 3) <= 1:
        score -= 5
    if features.get("family_hx_diabetes"):
        score -= 3
    if features.get("family_hx_heart"):
        score -= 3
    
    return max(10, min(100, round(score)))


# ════════════════════════════════════════════════════════════════
# 4. PREVENTIVE CARE — POSITIVE FRAMING
# ════════════════════════════════════════════════════════════════

def generate_preventive_care(features: dict) -> list[dict]:
    """Simple 2-line preventive care messages based on actual readings."""
    care_items = []

    if not features.get("has_vitals_data"):
        return care_items

    def item(category, urgency, status, message, steps, horizon):
        return {
            "category": category, "urgency": urgency,
            "current_status": status, "future_risk_message": message,
            "prevention_steps": steps, "risk_horizon": horizon
        }

    # ── Blood Pressure ──
    bp = features.get("bp_systolic_latest", features.get("bp_systolic_avg"))
    if bp is not None:
        if bp < 90:
            care_items.append(item("blood_pressure", "watch",
                f"BP low — {bp:.0f} mmHg",
                "Your BP is below normal. Drink more water and eat regular meals.",
                ["Drink 8-10 glasses of water daily", "Eat small frequent meals", "Rise slowly from sitting"],
                "Monitor daily"))
        elif bp <= 120:
            care_items.append(item("blood_pressure", "great",
                f"BP normal — {bp:.0f} mmHg",
                "Your blood pressure is healthy. Keep up your current habits.",
                ["Continue daily walks", "Maintain low-salt diet", "Stay hydrated"],
                "Keep it up"))
        elif bp < 130:
            care_items.append(item("blood_pressure", "watch",
                f"BP elevated — {bp:.0f} mmHg",
                "Slightly above normal. A 30-min daily walk can bring it down in 2 weeks.",
                ["Walk 30 min daily", "Reduce salt in meals", "Avoid packaged food"],
                "2-3 weeks"))
        elif bp < 140:
            care_items.append(item("blood_pressure", "focus",
                f"Stage 1 Hypertension — {bp:.0f} mmHg",
                "Needs attention. Lifestyle changes alone can fix this at this stage.",
                ["Walk 30 min daily", "Cut salt and packaged food", "Sleep by 10:30 PM", "Consult a doctor"],
                "4-6 weeks"))
        elif bp < 180:
            care_items.append(item("blood_pressure", "act_now",
                f"Stage 2 Hypertension — {bp:.0f} mmHg",
                "High BP needs medical attention. See a doctor this week.",
                ["See a doctor this week", "Walk daily", "Strictly reduce salt"],
                "Doctor visit needed"))
        else:
            care_items.append(item("blood_pressure", "act_now",
                f"Hypertensive Crisis — {bp:.0f} mmHg",
                "Critically high. Seek emergency care immediately.",
                ["Seek emergency care NOW"],
                "Emergency"))

    # ── Blood Sugar ──
    sugar = features.get("sugar_latest", features.get("sugar_avg"))
    if sugar is not None:
        if sugar < 54:
            care_items.append(item("blood_sugar", "act_now",
                f"Severe Low Sugar — {sugar:.0f} mg/dL",
                "Dangerously low. Eat sugar immediately and seek medical help.",
                ["Eat glucose or sugar immediately", "Seek emergency care"],
                "Immediate"))
        elif sugar < 70:
            care_items.append(item("blood_sugar", "focus",
                f"Low Blood Sugar — {sugar:.0f} mg/dL",
                "Below normal. Eat regular meals and never skip breakfast.",
                ["Never skip meals", "Carry a snack", "Consult a doctor if recurring"],
                "Monitor closely"))
        elif sugar < 100:
            care_items.append(item("blood_sugar", "great",
                f"Sugar normal — {sugar:.0f} mg/dL",
                "Your blood sugar is healthy. Keep your current diet and exercise.",
                ["Continue balanced diet", "Walk after meals", "Monitor monthly"],
                "Keep it up"))
        elif sugar < 126:
            care_items.append(item("blood_sugar", "watch",
                f"Prediabetes — {sugar:.0f} mg/dL",
                "Slightly high. Walk 10 min after meals and cut added sugar.",
                ["Walk 10 min after every meal", "Cut sugar in tea/coffee", "Switch to brown rice"],
                "8-12 weeks"))
        elif sugar <= 400:
            care_items.append(item("blood_sugar", "focus",
                f"Diabetes Range — {sugar:.0f} mg/dL",
                "Above normal. Consult a doctor and start lifestyle changes now.",
                ["Consult a doctor for HbA1c test", "Walk 30 min daily", "Avoid sugar and maida"],
                "Doctor visit needed"))
        else:
            care_items.append(item("blood_sugar", "act_now",
                f"Hyperglycemic Crisis — {sugar:.0f} mg/dL",
                "Critically high. Seek emergency care immediately.",
                ["Seek emergency care NOW"],
                "Emergency"))

    # ── Hemoglobin ──
    hb = features.get("hemoglobin")
    gender_enc = features.get("gender_enc", 1)
    hb_low = 13.5 if gender_enc == 1 else 12.0
    if hb is not None:
        if hb >= hb_low:
            care_items.append(item("hemoglobin", "great",
                f"Hemoglobin normal — {hb} g/dL",
                "Your hemoglobin is healthy. Good oxygen supply to all organs.",
                ["Continue iron-rich diet", "Stay active"],
                "Keep it up"))
        elif hb >= hb_low - 1.5:
            care_items.append(item("hemoglobin", "watch",
                f"Hemoglobin slightly low — {hb} g/dL",
                "Mildly low. Add iron-rich foods like spinach, dal, and dates daily.",
                ["Eat spinach, dal, eggs daily", "Eat citrus with iron foods", "Avoid tea after meals"],
                "6-8 weeks"))
        else:
            care_items.append(item("hemoglobin", "focus",
                f"Hemoglobin low — {hb} g/dL",
                "Below normal. Iron-rich diet and possible supplements needed.",
                ["Eat iron-rich food daily", "Consult doctor for iron supplements", "Vitamin C boosts absorption"],
                "6 weeks"))

    # ── Platelets ──
    platelets = features.get("platelet_count")
    if platelets is not None and platelets > 0:
        if platelets >= 150000:
            care_items.append(item("platelets", "great",
                f"Platelets normal — {platelets:,}/cumm",
                "Your platelet count is healthy.",
                ["Stay hydrated", "Eat balanced meals"],
                "Keep it up"))
        elif platelets >= 100000:
            care_items.append(item("platelets", "watch",
                f"Platelets borderline — {platelets:,}/cumm",
                "Slightly low. Retest in 2-3 weeks and eat papaya.",
                ["Retest CBC in 2-3 weeks", "Eat papaya daily", "Stay hydrated", "Avoid alcohol"],
                "2-3 weeks"))
        else:
            care_items.append(item("platelets", "act_now",
                f"Platelets low — {platelets:,}/cumm",
                "Needs medical attention. See a doctor soon.",
                ["See a doctor soon", "Eat papaya leaf extract", "Avoid aspirin/ibuprofen"],
                "Doctor visit needed"))

    # ── Cholesterol / LDL ──
    ldl = features.get("ldl")
    if ldl is not None and ldl > 100:
        if ldl >= 160:
            urgency, msg = "act_now", f"LDL {ldl} mg/dL is high. See a doctor — statin medication likely needed."
        elif ldl >= 130:
            urgency, msg = "focus", f"LDL {ldl} mg/dL needs attention. Cut fried food and add oats to your diet."
        else:
            urgency, msg = "watch", f"LDL {ldl} mg/dL is borderline. Reduce fried food and walk daily."
        care_items.append(item("cholesterol", urgency,
            f"LDL Cholesterol — {ldl} mg/dL", msg,
            ["Avoid fried food", "Eat oats and nuts daily", "Walk 30 min daily", "Consult doctor if above 130"],
            "8-12 weeks"))

    # ── Triglycerides ──
    trig = features.get("triglycerides")
    if trig is not None and trig > 150:
        if trig >= 500:
            urgency, msg = "act_now", f"Triglycerides {trig} mg/dL — very high, pancreatitis risk. See a doctor."
        elif trig >= 200:
            urgency, msg = "focus", f"Triglycerides {trig} mg/dL — high. Cut sugar and refined carbs now."
        else:
            urgency, msg = "watch", f"Triglycerides {trig} mg/dL — borderline. Reduce sugar and white rice."
        care_items.append(item("triglycerides", urgency,
            f"Triglycerides — {trig} mg/dL", msg,
            ["Cut added sugar completely", "Switch to brown rice or millets", "Avoid fruit juices", "Walk daily"],
            "6-8 weeks"))

    # ── HDL ──
    hdl = features.get("hdl")
    if hdl is not None and hdl < 40:
        care_items.append(item("cholesterol", "watch",
            f"HDL (good cholesterol) low — {hdl} mg/dL",
            "Low HDL increases heart risk. Exercise is the best way to raise it.",
            ["Walk or exercise daily", "Eat nuts and olive oil", "Reduce refined carbs"],
            "3 months"))

    # ── Thyroid ──
    tsh = features.get("tsh")
    if tsh is not None:
        if tsh > 4.5:
            care_items.append(item("thyroid", "focus" if tsh > 10 else "watch",
                f"TSH high — {tsh} mIU/L (Hypothyroidism)",
                "Thyroid is underactive. Causes fatigue and weight gain. Medication fixes this.",
                ["Consult doctor for Levothyroxine", "Retest TSH in 6-8 weeks", "Take medication on empty stomach"],
                "6-8 weeks"))
        elif tsh < 0.4:
            care_items.append(item("thyroid", "focus",
                f"TSH low — {tsh} mIU/L (Hyperthyroidism)",
                "Thyroid is overactive. Causes palpitations and weight loss. Needs evaluation.",
                ["Consult an endocrinologist", "Monitor heart rate", "Retest T3, T4"],
                "Medical evaluation"))

    # ── Liver (SGPT) ──
    sgpt = features.get("sgpt")
    if sgpt is not None and sgpt > 40:
        care_items.append(item("liver_health", "focus" if sgpt > 80 else "watch",
            f"SGPT/ALT elevated — {sgpt} U/L",
            "Liver is stressed. Avoid alcohol and fried food. Retest in 6-8 weeks.",
            ["Avoid alcohol completely", "Reduce fried and fatty food", "Retest in 6-8 weeks"],
            "6-8 weeks"))

    # ── Kidney (Creatinine) ──
    creatinine = features.get("creatinine")
    if creatinine is not None and creatinine > 1.2:
        care_items.append(item("kidney_health", "focus" if creatinine > 1.8 else "watch",
            f"Creatinine elevated — {creatinine} mg/dL",
            "Kidneys are under stress. Drink more water and reduce protein intake.",
            ["Drink 10+ glasses of water daily", "Reduce red meat", "Follow-up test in 3 months"],
            "3 months"))

    # ── RDW ──
    rdw = features.get("rdw")
    if rdw is not None and rdw > 14.5:
        care_items.append(item("hemoglobin", "watch",
            f"RDW elevated — {rdw}% (uneven red cells)",
            "Red cells vary in size — often iron or B12 deficiency. Easy to fix.",
            ["Get iron and B12 levels tested", "Eat iron-rich food daily", "Consider B12 supplement"],
            "6-8 weeks"))

    # ── Neutrophils ──
    neutrophils_pct = features.get("neutrophils_pct")
    if neutrophils_pct is not None and neutrophils_pct > 75:
        care_items.append(item("infection_markers", "watch",
            f"Neutrophils high — {neutrophils_pct}%",
            "Possible infection or stress response. Monitor for fever or pain.",
            ["Monitor for fever or pain", "Rest and stay hydrated", "Retest CBC in 2 weeks if no symptoms"],
            "1-2 weeks"))

    # ── Vitamin D ──
    vit_d = features.get("vitamin_d")
    if vit_d is not None and vit_d < 20:
        care_items.append(item("vitamins", "focus" if vit_d < 10 else "watch",
            f"Vitamin D deficient — {vit_d} ng/mL",
            "Low Vitamin D affects bones and immunity. Supplement and get morning sunlight.",
            ["Take Vitamin D3 supplement daily", "Get 15-20 min morning sunlight", "Retest in 3 months"],
            "3 months"))

    # ── Vitamin B12 ──
    vit_b12 = features.get("vitamin_b12")
    if vit_b12 is not None and vit_b12 < 200:
        care_items.append(item("vitamins", "focus" if vit_b12 < 100 else "watch",
            f"Vitamin B12 deficient — {vit_b12} pg/mL",
            "Low B12 causes fatigue and nerve issues. Supplement works quickly.",
            ["Take B12 supplement daily", "Eat eggs, dairy, or meat", "Retest in 3 months"],
            "3 months"))

    # ── BMI ──
    bmi = features.get("bmi")
    if bmi is not None:
        if features.get("bmi_class") == "overweight":
            care_items.append(item("weight_bmi", "watch",
                f"BMI {bmi} — slightly overweight",
                "Losing 3-5 kg improves BP, sugar, and energy. Small steps work.",
                ["Reduce portions by 20%", "Walk 30 min daily", "Replace sugary drinks with water"],
                "2-3 months"))
        elif features.get("bmi_class") == "obese":
            care_items.append(item("weight_bmi", "focus",
                f"BMI {bmi} — obese",
                "Weight needs attention. Consistent diet and exercise changes make a big difference.",
                ["Consult a doctor or dietitian", "Walk 30 min daily", "Cut fried food and sugar"],
                "3-6 months"))

    # ── Add risk_score and top_action ──
    urgency_score = {"great": 15, "watch": 42, "focus": 65, "act_now": 85}
    for c in care_items:
        c["risk_score"] = urgency_score.get(c["urgency"], 30)
        steps = c.get("prevention_steps", [])
        c["top_action"] = steps[0].upper() if steps else "MONITOR REGULARLY"

    return care_items



# ════════════════════════════════════════════════════════════════
# 5. DAILY TASK GENERATION — ONLY from actual data
# ════════════════════════════════════════════════════════════════

def generate_daily_tasks(features: dict, user) -> list[dict]:
    """
    Health-driven daily tasks:
    - Walk + Water: always (monitorable, coins)
    - CHECK_BP_7DAYS: if user has BP data (coins only after 7 days gap)
    - CHECK_SUGAR_7DAYS: if user has sugar data (coins only after 7 days gap)
    - Diet/lifestyle tips: based on vitals/BMI/report (coins=0, shown as tips)
    """
    tasks = []

    if not features.get("has_vitals_data"):
        return tasks

    bp_avg = features.get("bp_systolic_latest", features.get("bp_systolic_avg", 0)) or 0
    sugar_avg = features.get("sugar_avg", features.get("sugar_latest", 0)) or 0
    bmi = features.get("bmi") or 0
    hb = features.get("hemoglobin")
    platelets = features.get("platelet_count")

    # ── 1. Walk (always, monitorable) — uses user's step goal ──
    step_goal = getattr(user, 'step_goal', 6000) or 6000
    step_goal = max(6000, min(60000, int(step_goal)))
    walk_coins = round(25 + (step_goal - 6000) / (60000 - 6000) * 75)

    tasks.append({
        "task_type": "MORNING_WALK", "task_name": f"Walk {step_goal:,} steps today",
        "description": "A daily walk is the single best thing for your health",
        "why_this_task": "Daily walking improves BP, sugar, and mood simultaneously",
        "category": "exercise",
        "time_of_day": "morning", "duration_or_quantity": f"{step_goal:,} steps", "coins_reward": walk_coins
    })

    # ── 2. Water (tip only, not monitorable) ──
    glasses = 10 if bp_avg >= 130 else 8
    tasks.append({
        "task_type": "WATER_INTAKE", "task_name": f"Drink {glasses} glasses of water",
        "description": "Stay hydrated through the day",
        "why_this_task": "Hydration supports BP, kidney function, and overall health",
        "category": "wellness", "time_of_day": "all_day",
        "duration_or_quantity": f"{glasses} glasses", "coins_reward": 0
    })

    # BP elevated — low salt tip (Stage 1+)
    if bp_avg >= 130:
        tasks.append({
            "task_type": "LOW_SALT_MEAL", "task_name": "Go low-salt today",
            "description": "Use lemon and herbs instead of extra salt",
            "why_this_task": f"BP at {bp_avg:.0f} — cutting sodium can lower it noticeably this week",
            "category": "diet", "time_of_day": "all_day", "duration_or_quantity": "All meals", "coins_reward": 0
        })

    # Sugar elevated — post-meal walk tip (Prediabetes+)
    if sugar_avg >= 100:
        tasks.append({
            "task_type": "POST_MEAL_WALK", "task_name": "Walk 10 min after lunch",
            "description": "Short walk after eating reduces sugar spikes by 22%",
            "why_this_task": f"Sugar at {sugar_avg:.0f} mg/dL — post-meal walking is the #1 natural sugar control",
            "category": "exercise", "time_of_day": "afternoon", "duration_or_quantity": "10 minutes", "coins_reward": 0
        })

    # Low hemoglobin — iron-rich food tip
    if hb is not None:
        hb_low = 13.5 if features.get("gender_enc", 1) == 1 else 12.0
        if hb < hb_low:
            tasks.append({
                "task_type": "IRON_RICH_MEAL", "task_name": "Eat iron-rich food today",
                "description": "Spinach dal, dates, pomegranate, or eggs",
                "why_this_task": f"Hemoglobin at {hb} g/dL — daily iron-rich food boosts it naturally in 6 weeks",
                "category": "diet", "time_of_day": "lunch", "duration_or_quantity": "1 iron-rich meal", "coins_reward": 0
            })

    # Low platelets — papaya tip
    if platelets is not None and 0 < platelets < 150000:
        tasks.append({
            "task_type": "EAT_PAPAYA", "task_name": "Eat fresh papaya today",
            "description": "Papaya supports natural platelet production",
            "why_this_task": f"Platelets at {int(platelets):,} — papaya is linked to platelet recovery",
            "category": "diet", "time_of_day": "afternoon", "duration_or_quantity": "1 bowl", "coins_reward": 0
        })

    # High BMI — portion control tip
    if bmi > 27:
        tasks.append({
            "task_type": "PORTION_CONTROL", "task_name": "Reduce portions by 20% today",
            "description": "Use a slightly smaller plate",
            "why_this_task": f"BMI {bmi:.1f} — small portion reduction leads to sustainable weight loss",
            "category": "diet", "time_of_day": "all_day", "duration_or_quantity": "All meals", "coins_reward": 0
        })

    # High LDL — dietary tip
    ldl = features.get("ldl")
    if ldl is not None and ldl > 130:
        tasks.append({
            "task_type": "LOW_FAT_MEAL", "task_name": "Avoid fried food today",
            "description": "Choose baked, grilled, or steamed options",
            "why_this_task": f"LDL at {ldl} mg/dL — cutting saturated fat reduces it in 8 weeks",
            "category": "diet", "time_of_day": "all_day", "duration_or_quantity": "All meals", "coins_reward": 0
        })

    # High triglycerides — sugar reduction tip
    triglycerides = features.get("triglycerides")
    if triglycerides is not None and triglycerides > 150:
        tasks.append({
            "task_type": "NO_SUGAR_DAY", "task_name": "Skip added sugar today",
            "description": "No sugar in tea, coffee, or snacks",
            "why_this_task": f"Triglycerides at {triglycerides} mg/dL — sugar is the #1 driver",
            "category": "diet", "time_of_day": "all_day", "duration_or_quantity": "All day", "coins_reward": 0
        })

    return tasks


# ════════════════════════════════════════════════════════════════
# 6. DIET PLAN — Personalized from ALL data
# ════════════════════════════════════════════════════════════════

def generate_diet_plan(features: dict) -> dict | None:
    """
    Returns None if no vitals data exists (no diet to show).
    Otherwise, personalized diet from ALL health data.
    """
    if not features.get("has_vitals_data"):
        return None
    
    bmi = features.get("bmi")
    bp_avg = features.get("bp_systolic_latest", features.get("bp_systolic_avg"))
    sugar_avg = features.get("sugar_latest", features.get("sugar_avg"))
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
    
    if bp_avg is not None and bp_avg >= 120:
        focus_parts.append("heart_healthy")
        reason_parts.append(f"Supporting your BP ({bp_avg:.0f} mmHg)")
        eat_more.extend([
            "Banana — natural potassium counters sodium",
            "Spinach and leafy greens",
            "Garlic — natural BP support",
            "Oats — helps reduce BP over time"
        ])
        reduce.extend(["Extra salt — try lemon and herbs instead", "Tea/coffee to 1-2 cups daily"])
        avoid.extend(["Pickles and papad", "Packaged chips and namkeen", "Instant noodles"])
        hydration = max(hydration, 10)
    
    if sugar_avg is not None and sugar_avg >= 100:
        focus_parts.append("sugar_smart")
        reason_parts.append(f"Helping your sugar levels ({sugar_avg:.0f} mg/dL)")
        eat_more.extend([
            "Brown rice or millets (ragi, jowar, bajra)",
            "Bitter gourd — natural sugar support",
            "Methi seeds — soak overnight, eat morning",
            "Nuts as snacks (almonds, walnuts)"
        ])
        reduce.extend(["White rice to half a cup", "Only low-GI fruits (apple, guava)"])
        avoid.extend(["Sugar in tea/coffee", "Fruit juices (even fresh ones)", "Maida products"])
    
    if hb is not None and hb < hb_low:
        focus_parts.append("iron_boost")
        reason_parts.append(f"Building up your hemoglobin ({hb} g/dL)")
        eat_more.extend([
            "Spinach, palak, methi daily",
            "Rajma, chana, masoor dal",
            "Jaggery instead of sugar",
            "Pomegranate and beetroot"
        ])
        reduce.extend(["Tea right after meals — blocks iron"])
        hydration = max(hydration, 9)
    
    if platelets is not None and 0 < platelets < 150000:
        focus_parts.append("platelet_support")
        reason_parts.append(f"Supporting platelet recovery ({platelets:,})")
        eat_more.extend([
            "Fresh papaya",
            "Pomegranate seeds and juice",
            "Pumpkin and pumpkin seeds"
        ])
        avoid.extend(["Alcohol completely"])
        hydration = max(hydration, 10)
    
    if bmi is not None and bmi >= 27:
        focus_parts.append("weight_friendly")
        reason_parts.append(f"Supporting your weight goals (BMI {bmi})")
        eat_more.extend([
            "Protein-rich breakfast (eggs, paneer)",
            "Salad before each meal",
            "Green tea instead of milk tea"
        ])
        reduce.extend(["Portion sizes by 20%", "Fried food to twice a week"])
        avoid.extend(["Late night snacking", "Sugary drinks"])
    
    # Report glucose-based additions
    report_glucose = features.get("fasting_glucose_report")
    if report_glucose and report_glucose >= 100 and not features.get("has_sugar_data"):
        focus_parts.append("sugar_smart")
        reason_parts.append(f"Report shows glucose at {report_glucose:.0f} mg/dL")
        eat_more.extend([
            "Whole grains and millets",
            "Nuts and seeds as snacks"
        ])
        avoid.extend(["Refined sugar and sweets"])
    
    if not focus_parts:
        focus_parts.append("balanced_wellness")
        reason_parts.append("Maintaining your healthy vitals")
        eat_more.extend([
            "Seasonal vegetables with every meal",
            "2-3 fruits daily",
            "Whole grains instead of refined",
            "Lean protein with every meal"
        ])
        reduce.extend(["Fried foods to twice a week", "Packaged food"])
        avoid.extend(["Sugary drinks", "Trans fats"])
    
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
# 7. PERSISTENCE
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
    # 1. Fetch completed tasks for today so we don't recreate them
    result = await db.execute(
        select(DailyTask)
        .where(DailyTask.user_id == user_id)
        .where(DailyTask.task_date == datetime.date.today())
        .where(DailyTask.completed == True)
    )
    completed_tasks = result.scalars().all()
    completed_types = {t.task_type for t in completed_tasks}

    # 2. Delete all INCOMPLETE tasks for today
    await db.execute(
        delete(DailyTask)
        .where(DailyTask.user_id == user_id)
        .where(DailyTask.task_date == datetime.date.today())
        .where(DailyTask.completed == False)
    )
    
    # 3. Add new tasks ONLY if they haven't been completed today
    for t in task_list:
        if t["task_type"] in completed_types:
            continue
            
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

async def save_diet(user_id: str, diet: dict | None, db: AsyncSession):
    await db.execute(delete(DietRecommendation).where(DietRecommendation.user_id == user_id))
    if diet is None:
        return
    obj = DietRecommendation(
        user_id=user_id,
        focus_type=diet["focus_type"][:50],
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
    MASTER PIPELINE: ALL data -> Features -> Tasks + Care + Diet.
    Called after: BP log, Sugar log, BMI update, Report upload.
    """
    user = await get_user(user_id, db)
    if not user:
        print(f"❌ run_full_analysis: User {user_id} not found")
        return None
    
    bp_readings = await get_bp_readings(user_id, db)
    sugar_readings = await get_sugar_readings(user_id, db)
    latest_report = await get_latest_report(user_id, db)
    
    print(f"\n{'='*60}")
    print(f"[ANALYSIS] PIPELINE for {user.full_name} ({user_id[:8]}...)")
    print(f"   BP readings: {len(bp_readings)}")
    print(f"   Sugar readings: {len(sugar_readings)}")
    print(f"   Has report: {latest_report is not None}")
    if latest_report:
        print(f"   Report data: Hb={latest_report.hemoglobin}, Platelets={latest_report.platelet_count}, "
              f"Glucose={latest_report.fasting_glucose}")
    
    features = build_features(user, bp_readings, sugar_readings, latest_report)
    
    print(f"   Features: has_vitals={features.get('has_vitals_data')}, "
          f"has_bp={features.get('has_bp_data')}, "
          f"has_sugar={features.get('has_sugar_data')}, "
          f"has_report={features.get('has_report')}")
    print(f"   BMI={features.get('bmi')}, BP_avg={features.get('bp_systolic_avg')}, "
          f"Sugar_avg={features.get('sugar_avg')}, Hb={features.get('hemoglobin')}")
    
    health_index = calculate_health_index(features)
    preventive = generate_preventive_care(features)
    tasks = generate_daily_tasks(features, user)
    diet = generate_diet_plan(features)
    
    print(f"   -> Health Index: {health_index}")
    print(f"   -> Preventive items: {len(preventive)} [{', '.join(c['category'] for c in preventive)}]")
    print(f"   -> Tasks generated: {len(tasks)} [{', '.join(t['task_name'][:25] for t in tasks)}]")
    print(f"   -> Diet plan: {diet.get('focus_type') if diet else 'None'}")
    print(f"{'='*60}\n")
    
    await save_preventive_care(user_id, preventive, db)
    await replace_todays_tasks(user_id, tasks, db)
    await save_diet(user_id, diet, db)
    await update_analysis_status(user_id, db)
    # Flush to DB (caller is responsible for commit)
    await db.flush()
    
    return {
        "health_index": health_index,
        "preventive_care": preventive,
        "tasks": tasks,
        "diet": diet
    }
