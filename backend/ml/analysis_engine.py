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
        f["hemoglobin"] = float(report.hemoglobin) if report.hemoglobin else None
        f["rbc_count"] = float(report.rbc_count) if report.rbc_count else None
        f["wbc_count"] = int(report.wbc_count) if report.wbc_count else None
        f["platelet_count"] = int(report.platelet_count) if report.platelet_count else None
        f["fasting_glucose_report"] = float(report.fasting_glucose) if report.fasting_glucose else None
        f["creatinine"] = float(report.creatinine) if report.creatinine else None
        f["urea"] = float(report.urea) if report.urea else None
    else:
        f["hemoglobin"] = None
        f["platelet_count"] = None
    
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
    bp_avg = features.get("bp_systolic_avg")
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
    sugar_avg = features.get("sugar_avg")
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
    """
    POSITIVE FARMING approach:
    - Lead with what's going well
    - Frame risks as opportunities
    - Every message ends with empowerment
    """
    care_items = []
    
    # Only generate if we have actual vitals data
    if not features.get("has_vitals_data"):
        return care_items
    
    # ── BP Care ──
    bp_avg = features.get("bp_systolic_avg")
    if bp_avg is not None:
        bp_trend = features.get("bp_trend", "steady")
        
        if bp_avg < 120:
            care_items.append({
                "category": "blood_pressure",
                "urgency": "great",
                "current_status": f"Healthy BP — {bp_avg:.0f} mmHg avg 💚",
                "future_risk_message": (
                    "Your blood pressure is in an excellent range! "
                    "You're doing something right — keep up the active lifestyle. "
                    "People who maintain BP below 120 have 40% lower heart risk over 10 years."
                ),
                "prevention_steps": [
                    "Keep enjoying your daily walks",
                    "Your sodium habits are working well",
                    "Stay hydrated — you're on the right track"
                ],
                "risk_horizon": "You're in the safe zone 🎯"
            })
        elif bp_avg < 130:
            care_items.append({
                "category": "blood_pressure",
                "urgency": "watch",
                "current_status": f"BP slightly elevated — {bp_avg:.0f} mmHg avg",
                "future_risk_message": (
                    f"Your BP is slightly above ideal (trend: {bp_trend}). "
                    "Great news — this is the easiest stage to bring it back to normal! "
                    "Simple changes like a 30-minute walk and cutting extra salt "
                    "can drop it 5-8 mmHg in just 2 weeks."
                ),
                "prevention_steps": [
                    "A 30-min morning walk can bring this down naturally",
                    "Try lemon instead of extra salt — tastes great too!",
                    "Deep breathing for 5 min helps more than you think",
                    "You're catching this early — that's the smart move"
                ],
                "risk_horizon": "2-3 weeks of simple changes can fix this"
            })
        elif bp_avg < 140:
            care_items.append({
                "category": "blood_pressure",
                "urgency": "focus",
                "current_status": f"BP needs attention — {bp_avg:.0f} mmHg avg",
                "future_risk_message": (
                    "Your BP needs some focus, but here's the encouraging part: "
                    "at this level, lifestyle changes ALONE can bring it back to normal. "
                    "Walking, eating right, and sleeping well are powerful medicine."
                ),
                "prevention_steps": [
                    "Start with a daily 30-min walk — it works like medication",
                    "Cut packaged foods this week — they're loaded with hidden salt",
                    "Sleep by 10:30 PM — your body repairs BP during sleep",
                    "You've taken the first step by tracking — that's half the battle"
                ],
                "risk_horizon": "4-6 weeks of consistent effort"
            })
        else:
            care_items.append({
                "category": "blood_pressure",
                "urgency": "act_now",
                "current_status": f"BP elevated — {bp_avg:.0f} mmHg avg",
                "future_risk_message": (
                    "Your BP is higher than ideal, but you're already taking the right steps "
                    "by tracking it. Many people bring their BP down significantly with "
                    "consistent daily walking and dietary changes. A check-in with your "
                    "doctor can give you a clear action plan."
                ),
                "prevention_steps": [
                    "A doctor visit this week will give you clarity and confidence",
                    "Walking daily is the single most effective natural treatment",
                    "Reducing salt for just 2 weeks shows measurable improvement",
                    "You're monitoring — that puts you ahead of 90% of people"
                ],
                "risk_horizon": "Doctor guidance + lifestyle = fast results"
            })
    
    # ── Sugar Care ──
    sugar_avg = features.get("sugar_avg")
    if sugar_avg is not None:
        sugar_trend = features.get("sugar_trend", "steady")
        
        if sugar_avg < 100:
            care_items.append({
                "category": "blood_sugar",
                "urgency": "great",
                "current_status": f"Healthy sugar — {sugar_avg:.0f} mg/dL avg 💚",
                "future_risk_message": (
                    "Your fasting sugar is in the healthy zone! "
                    "This means your body is managing glucose efficiently. "
                    "Keep up your current eating and exercise habits — they're working."
                ),
                "prevention_steps": [
                    "Your diet choices are keeping sugar in check",
                    "Post-meal walks are a great habit to continue",
                    "Regular monitoring keeps you in control"
                ],
                "risk_horizon": "You're in the safe zone 🎯"
            })
        elif sugar_avg < 126:
            care_items.append({
                "category": "blood_sugar",
                "urgency": "watch",
                "current_status": f"Sugar slightly elevated — {sugar_avg:.0f} mg/dL avg",
                "future_risk_message": (
                    f"Your sugar is slightly above the ideal range (trend: {sugar_trend}). "
                    "The fantastic news? Research shows that at this stage, "
                    "lifestyle changes can fully reverse the trend in 8-12 weeks. "
                    "You have complete control here."
                ),
                "prevention_steps": [
                    "Switch to brown rice or millets — they taste great and help a lot",
                    "A 10-min walk after meals reduces sugar spikes by 22%",
                    "Try nuts as snacks instead of biscuits — equally satisfying",
                    "You caught this early — that's the smartest health decision"
                ],
                "risk_horizon": "8-12 weeks of dietary changes can reverse this"
            })
        else:
            care_items.append({
                "category": "blood_sugar",
                "urgency": "focus",
                "current_status": f"Sugar needs focus — {sugar_avg:.0f} mg/dL avg",
                "future_risk_message": (
                    "Your sugar is above the ideal range, but you're already tracking it — "
                    "that's the most important step. Many people in this range bring their "
                    "sugar back to normal with consistent dietary changes and exercise. "
                    "A doctor can also help you create a personalized plan."
                ),
                "prevention_steps": [
                    "Visit your doctor for an HbA1c test — it gives the 3-month picture",
                    "Walking 30 min daily is as powerful as some medications",
                    "Eating dinner before 7:30 PM helps your body process sugar better",
                    "Small, frequent meals keep sugar more stable than big ones"
                ],
                "risk_horizon": "Doctor guidance + diet changes work best together"
            })
    
    # ── BMI Care ──
    bmi = features.get("bmi")
    if bmi is not None:
        weight = features.get("weight_kg", 0)
        
        if features.get("bmi_class") == "overweight":
            care_items.append({
                "category": "weight_bmi",
                "urgency": "watch",
                "current_status": f"BMI {bmi} — room for improvement",
                "future_risk_message": (
                    f"Your BMI is {bmi}, which is slightly above ideal. "
                    "Here's the encouraging part: losing just 3-5 kg can "
                    "reduce your BP by 5 mmHg AND improve your sugar levels. "
                    "Small, sustainable changes work better than crash diets."
                ),
                "prevention_steps": [
                    "Reduce portion sizes by just 20% — you won't even notice",
                    "Add a salad before lunch — it fills you up naturally",
                    "Replace sugary drinks with water or buttermilk",
                    "Walking 10,000 steps is the easiest weight loss tool"
                ],
                "risk_horizon": "3-5 kg loss in 2-3 months makes a big difference"
            })
        elif features.get("bmi_class") == "obese":
            care_items.append({
                "category": "weight_bmi",
                "urgency": "focus",
                "current_status": f"BMI {bmi} — needs your attention",
                "future_risk_message": (
                    "Your weight needs some focus, and the best approach is "
                    "gradual, sustainable changes. A doctor can help create "
                    "a plan that works for YOUR body and lifestyle."
                ),
                "prevention_steps": [
                    "Start with a 20-min walk daily — build up gradually",
                    "A doctor can help with a personalized weight plan",
                    "Focus on protein-rich breakfast — reduces cravings all day",
                    "Good sleep (7-8 hrs) prevents stress-related weight gain"
                ],
                "risk_horizon": "Start small — every kg lost helps"
            })
    
    # ── Hemoglobin Care (from Report) ──
    hb = features.get("hemoglobin")
    if hb is not None:
        gender_enc = features.get("gender_enc", 1)
        hb_low = 13.5 if gender_enc == 1 else 12.0
        
        if hb >= hb_low:
            care_items.append({
                "category": "hemoglobin",
                "urgency": "great",
                "current_status": f"Healthy hemoglobin — {hb} g/dL 💚",
                "future_risk_message": (
                    "Your hemoglobin is in a healthy range! This means good oxygen "
                    "delivery to all your organs. Your diet is working well."
                ),
                "prevention_steps": [
                    "Your iron intake is on point — keep it up",
                    "Continue eating green leafy vegetables",
                    "Vitamin C with meals helps maintain iron levels"
                ],
                "risk_horizon": "You're in the safe zone 🎯"
            })
        elif hb >= hb_low - 1.5:
            care_items.append({
                "category": "hemoglobin",
                "urgency": "watch",
                "current_status": f"Hemoglobin slightly low — {hb} g/dL",
                "future_risk_message": (
                    f"Your hemoglobin ({hb} g/dL) is slightly below ideal. "
                    "This is very common and easily fixable with food! "
                    "Iron-rich foods can bring it back to normal in 6-8 weeks."
                ),
                "prevention_steps": [
                    "Add spinach, dal, or eggs to daily meals",
                    "Jaggery and dates make great iron-rich snacks",
                    "Eat citrus fruit with iron foods — boosts absorption 3x",
                    "Avoid tea right after meals — it blocks iron"
                ],
                "risk_horizon": "6-8 weeks with dietary changes"
            })
        else:
            care_items.append({
                "category": "hemoglobin",
                "urgency": "focus",
                "current_status": f"Hemoglobin needs attention — {hb} g/dL",
                "future_risk_message": (
                    f"Your hemoglobin is at {hb} g/dL, which is below normal. "
                    "This could be causing fatigue. The good news — iron supplements "
                    "and dietary changes can fix this effectively. A doctor can confirm "
                    "the best approach for you."
                ),
                "prevention_steps": [
                    "A simple blood test can pinpoint the cause",
                    "Iron-rich foods: spinach, lentils, jaggery, dates, pomegranate",
                    "An iron supplement (if doctor advises) works in 6 weeks",
                    "Vitamin C foods help your body absorb iron better"
                ],
                "risk_horizon": "6 weeks with proper iron intake"
            })
    
    # ── Platelet Care (from Report) ──
    platelets = features.get("platelet_count")
    if platelets is not None and platelets > 0:
        if platelets >= 150000:
            care_items.append({
                "category": "platelets",
                "urgency": "great",
                "current_status": f"Healthy platelets — {platelets:,}/cumm 💚",
                "future_risk_message": "Your platelet count is in the healthy range!",
                "prevention_steps": [
                    "Your body is producing platelets well",
                    "Stay hydrated and eat balanced meals"
                ],
                "risk_horizon": "You're in the safe zone 🎯"
            })
        elif platelets >= 100000:
            care_items.append({
                "category": "platelets",
                "urgency": "watch",
                "current_status": f"Platelets slightly low — {platelets:,}/cumm",
                "future_risk_message": (
                    "Your platelets are slightly below the ideal range. "
                    "This is often temporary. A retest in 2-3 weeks can confirm. "
                    "Papaya and pomegranate are traditionally known to help."
                ),
                "prevention_steps": [
                    "Retest CBC in 2-3 weeks to confirm",
                    "Eat papaya and pomegranate — they support platelet production",
                    "Stay well hydrated — 10+ glasses daily",
                    "Avoid alcohol until retest"
                ],
                "risk_horizon": "2-3 weeks for retest"
            })
        else:
            care_items.append({
                "category": "platelets",
                "urgency": "act_now",
                "current_status": f"Platelets need medical attention — {platelets:,}/cumm",
                "future_risk_message": (
                    "Your platelet count needs a doctor's attention. This could be "
                    "temporary and often resolves with treatment. A doctor visit "
                    "will help you understand the cause and get the right care."
                ),
                "prevention_steps": [
                    "See your doctor in the next few days for guidance",
                    "Eat papaya leaf extract — it's a natural helper",
                    "Stay hydrated and avoid aspirin/ibuprofen",
                    "Avoid activities with high injury risk until platelets improve"
                ],
                "risk_horizon": "Doctor visit recommended soon"
            })
    
    # ── Creatinine/Kidney Care (from Report) ──
    creatinine = features.get("creatinine")
    if creatinine is not None and creatinine > 1.2:
        care_items.append({
            "category": "kidney_health",
            "urgency": "watch",
            "current_status": f"Creatinine slightly elevated — {creatinine} mg/dL",
            "future_risk_message": (
                "Your creatinine is slightly above normal, which means your kidneys "
                "are working a bit harder. Stay well hydrated and reduce protein-heavy "
                "meals. A doctor can guide you on monitoring this."
            ),
            "prevention_steps": [
                "Drink 10+ glasses of water daily — your kidneys will thank you",
                "Reduce red meat and heavy protein meals",
                "A follow-up kidney function test in 3 months is wise",
                "Control BP and sugar — they directly protect kidneys"
            ],
            "risk_horizon": "3-month follow-up retest"
        })
    
    # ── Post-process: add risk_score (%) and top_action ──
    urgency_to_score = {
        "great": lambda: 15,   # Low risk
        "watch": lambda: 42,   # Moderate
        "focus": lambda: 65,   # Needs focus
        "act_now": lambda: 85  # High
    }
    
    for item in care_items:
        base = urgency_to_score.get(item["urgency"], lambda: 30)()
        
        # Fine-tune based on actual data
        cat = item["category"]
        if cat == "blood_pressure":
            bp_avg = features.get("bp_systolic_avg", 120)
            if bp_avg and bp_avg > 0:
                item["risk_score"] = min(95, max(10, int((bp_avg - 90) / 0.8)))
            else:
                item["risk_score"] = base
        elif cat == "blood_sugar":
            sugar_avg = features.get("sugar_avg", 90)
            if sugar_avg and sugar_avg > 0:
                item["risk_score"] = min(95, max(10, int((sugar_avg - 60) / 1.5)))
            else:
                item["risk_score"] = base
        elif cat == "hemoglobin":
            hb = features.get("hemoglobin")
            if hb:
                hb_low = 13.5 if features.get("gender_enc") == 1 else 12.0
                item["risk_score"] = min(90, max(10, int(100 - (hb / hb_low) * 80)))
            else:
                item["risk_score"] = base
        elif cat == "weight_bmi":
            bmi = features.get("bmi", 25)
            if bmi:
                item["risk_score"] = min(85, max(10, int((bmi - 18) * 5)))
            else:
                item["risk_score"] = base
        else:
            item["risk_score"] = base
        
        # Top action from first prevention step
        steps = item.get("prevention_steps", [])
        item["top_action"] = steps[0] if steps else "Monitor regularly"
    
    return care_items


# ════════════════════════════════════════════════════════════════
# 5. DAILY TASK GENERATION — ONLY from actual data
# ════════════════════════════════════════════════════════════════

def generate_daily_tasks(features: dict, user) -> list[dict]:
    """
    RULES:
    1. NO tasks before user has any vitals data
    2. Tasks are SPECIFIC to the data we have
    3. Each task explains WHY it's recommended
    """
    tasks = []
    
    # ── EXIT if no vitals data exists ──
    if not features.get("has_vitals_data"):
        return tasks  # Empty — dashboard will show the empty state card
    
    # ── BP-Based Tasks (ONLY if user has logged BP) ──
    if features.get("has_bp_data"):
        bp_avg = features.get("bp_systolic_avg", 120)
        
        if bp_avg >= 130:
            tasks.append({
                "task_type": "MORNING_WALK",
                "task_name": "Walk 10,000 steps today",
                "description": "A brisk morning walk — your best BP medicine",
                "why_this_task": f"Your BP avg is {bp_avg:.0f}. Walking for 30 min can reduce it by 5-8 mmHg naturally",
                "category": "exercise",
                "time_of_day": "morning",
                "duration_or_quantity": "30 min / 10,000 steps",
                "coins_reward": 20
            })
            tasks.append({
                "task_type": "LOW_SALT_MEAL",
                "task_name": "Go low-salt today",
                "description": "Use lemon and herbs instead of extra salt",
                "why_this_task": f"BP at {bp_avg:.0f} — cutting sodium this week can lower it noticeably",
                "category": "diet",
                "time_of_day": "all_day",
                "duration_or_quantity": "All meals today",
                "coins_reward": 12
            })
        elif bp_avg >= 120:
            tasks.append({
                "task_type": "MORNING_WALK",
                "task_name": "Walk 7,000 steps today",
                "description": "Stay active to keep your BP in the healthy zone",
                "why_this_task": f"Your BP is {bp_avg:.0f} — regular walking prevents it from creeping up",
                "category": "exercise",
                "time_of_day": "morning",
                "duration_or_quantity": "25 min / 7,000 steps",
                "coins_reward": 15
            })
        else:
            tasks.append({
                "task_type": "MORNING_WALK",
                "task_name": "Daily walk — keep it up!",
                "description": "Your BP is great, walking keeps it that way",
                "why_this_task": "BP is healthy! Walking maintains it and boosts energy",
                "category": "exercise",
                "time_of_day": "morning",
                "duration_or_quantity": "20 min / 5,000 steps",
                "coins_reward": 12
            })
    
    # ── Sugar-Based Tasks (ONLY if user has logged sugar) ──
    if features.get("has_sugar_data"):
        sugar_avg = features.get("sugar_avg", 100)
        
        if sugar_avg >= 100:
            tasks.append({
                "task_type": "POST_MEAL_WALK",
                "task_name": "Walk 10 min after lunch",
                "description": "This one habit reduces sugar spikes by 22%",
                "why_this_task": f"Sugar at {sugar_avg:.0f} mg/dL — post-meal walking is the #1 natural sugar control",
                "category": "exercise",
                "time_of_day": "afternoon",
                "duration_or_quantity": "10 minutes after eating",
                "coins_reward": 10
            })
            tasks.append({
                "task_type": "NO_SUGAR_DAY",
                "task_name": "Skip added sugar today",
                "description": "No sugar in tea, coffee, or snacks",
                "why_this_task": f"Fasting glucose at {sugar_avg:.0f} — reducing added sugar can lower it by 8-12 mg/dL in 3 weeks",
                "category": "diet",
                "time_of_day": "all_day",
                "duration_or_quantity": "All day",
                "coins_reward": 12
            })
        else:
            tasks.append({
                "task_type": "BALANCED_MEALS",
                "task_name": "Eat balanced meals today",
                "description": "Include protein, fibre, and vegetables with each meal",
                "why_this_task": "Your sugar is healthy! A balanced diet keeps it stable",
                "category": "diet",
                "time_of_day": "all_day",
                "duration_or_quantity": "3 balanced meals",
                "coins_reward": 8
            })
    
    # ── Report-Based Tasks (ONLY if user has uploaded a report) ──
    if features.get("has_report"):
        hb = features.get("hemoglobin")
        if hb is not None:
            hb_low = 13.5 if features.get("gender_enc") == 1 else 12.0
            if hb < hb_low:
                tasks.append({
                    "task_type": "IRON_RICH_MEAL",
                    "task_name": "Eat iron-rich food today",
                    "description": "Spinach dal, dates, pomegranate, or eggs",
                    "why_this_task": f"Hemoglobin at {hb} g/dL — daily iron-rich food naturally boosts it in 6 weeks",
                    "category": "diet",
                    "time_of_day": "lunch",
                    "duration_or_quantity": "At least 1 iron-rich meal",
                    "coins_reward": 10
                })
        
        platelets = features.get("platelet_count")
        if platelets is not None and 0 < platelets < 150000:
            tasks.append({
                "task_type": "EAT_PAPAYA",
                "task_name": "Eat fresh papaya today",
                "description": "Papaya supports natural platelet production",
                "why_this_task": f"Platelets at {platelets:,} — papaya is traditionally linked to platelet recovery",
                "category": "diet",
                "time_of_day": "afternoon",
                "duration_or_quantity": "1 bowl fresh papaya",
                "coins_reward": 8
            })
        
        # Report-based glucose task
        report_glucose = features.get("fasting_glucose_report")
        if report_glucose and report_glucose >= 100 and not features.get("has_sugar_data"):
            tasks.append({
                "task_type": "POST_MEAL_WALK",
                "task_name": "Walk after meals",
                "description": "Your report shows elevated glucose — walking helps control it",
                "why_this_task": f"Report glucose at {report_glucose:.0f} mg/dL — post-meal walks reduce spikes by 22%",
                "category": "exercise",
                "time_of_day": "afternoon",
                "duration_or_quantity": "10 min after each meal",
                "coins_reward": 10
            })
    
    # ── BMI-Based Tasks ──
    bmi = features.get("bmi")
    if bmi is not None and bmi > 27:
        tasks.append({
            "task_type": "PORTION_CONTROL",
            "task_name": "Reduce portions by 20% today",
            "description": "Use a slightly smaller plate — you won't miss it",
            "why_this_task": f"BMI is {bmi} — small portion reduction leads to sustainable weight loss",
            "category": "diet",
            "time_of_day": "all_day",
            "duration_or_quantity": "All meals",
            "coins_reward": 10
        })
    
    # ── Hydration (ONLY when tasks exist from other sources) ──
    if len(tasks) > 0:
        hydration_glasses = 8
        if features.get("bp_systolic_avg") and features["bp_systolic_avg"] >= 130:
            hydration_glasses = 10
        if features.get("platelet_count") and features["platelet_count"] < 150000:
            hydration_glasses = 10
        
        tasks.append({
            "task_type": "WATER_INTAKE",
            "task_name": f"Drink {hydration_glasses} glasses of water",
            "description": "Stay hydrated through the day",
            "why_this_task": "Hydration supports BP, kidney function, and overall health",
            "category": "wellness",
            "time_of_day": "all_day",
            "duration_or_quantity": f"{hydration_glasses} glasses (250ml each)",
            "coins_reward": 8
        })
    
    # ── Stress-Based Tasks ──
    stress = features.get("stress_level", 5)
    if stress >= 7 and len(tasks) > 0:
        tasks.append({
            "task_type": "DEEP_BREATHING",
            "task_name": "5-min deep breathing",
            "description": "Slow belly breathing — calms your nervous system",
            "why_this_task": f"Stress level {stress}/10 — deep breathing lowers cortisol and BP within minutes",
            "category": "wellness",
            "time_of_day": "evening",
            "duration_or_quantity": "5 minutes",
            "coins_reward": 5
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
    # Delete ALL tasks for today — fresh analysis replaces everything
    await db.execute(
        delete(DailyTask)
        .where(DailyTask.user_id == user_id)
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

async def save_diet(user_id: str, diet: dict | None, db: AsyncSession):
    await db.execute(delete(DietRecommendation).where(DietRecommendation.user_id == user_id))
    if diet is None:
        return
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
    print(f"🔬 ANALYSIS PIPELINE for {user.full_name} ({user_id[:8]}...)")
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
    
    print(f"   → Health Index: {health_index}")
    print(f"   → Preventive items: {len(preventive)} [{', '.join(c['category'] for c in preventive)}]")
    print(f"   → Tasks generated: {len(tasks)} [{', '.join(t['task_name'][:25] for t in tasks)}]")
    print(f"   → Diet plan: {diet.get('focus_type') if diet else 'None'}")
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
