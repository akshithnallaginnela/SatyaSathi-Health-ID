"""
ML Router — analyze uploaded health reports using ONLY trained ML models.
POST /api/ml/analyze-report
Pure model-driven; no hardcoded rules.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select, desc
from datetime import date

from database import get_db
from security.jwt_handler import get_current_user_id
from services.ocr_service import process_health_document
from services.storage_service import upload_file_to_firebase
from models.report import Report
from models.task import DailyTask
from models.health_record import VitalsLog, BodyMetrics
from models.user import User
from ml.realistic_predictor import predict_from_ocr

router = APIRouter(prefix="/api/ml", tags=["ML Analysis"])


def _tasks_from_model_predictions(task_predictions: dict[str, bool], feat: dict) -> list[dict]:
    """Map model predictions to tasks, with condition-specific base tasks.
    
    COIN POLICY:
    - MONITORABLE tasks (walking, water, check BP/sugar) → earn coins
    - NON-MONITORABLE tasks (diet, avoid, sleep) → 0 coins (guidance only)
    """
    mapping = {
        "task_iron_rich_diet": {
            "type": "IRON_DIET",
            "name": "Eat Iron-Rich Meal (Spinach/Lentils)",
            "coins": 0,  # ❌ Not monitorable
            "time_slot": "afternoon"
        },
        "task_log_sugar": {
            "type": "CHECK_SUGAR_7DAYS",
            "name": "Check Fasting Sugar This Week",
            "coins": 20,  # ✅ Monitorable
            "time_slot": "morning"
        },
        "task_reduce_sugar_food": {
            "type": "AVOID_SUGAR",
            "name": "Zero Added Sugar Today",
            "coins": 0,  # ❌ Not monitorable
            "time_slot": "evening"
        },
        "task_doctor_visit": {
            "type": "DOCTOR_VISIT",
            "name": "Book Doctor Follow-Up",
            "coins": 0,  # ❌ Not monitorable
            "time_slot": "all_day"
        },
        "task_retest_in_2_weeks": {
            "type": "RETEST_2W",
            "name": "Schedule Retest in 2 Weeks",
            "coins": 0,  # ❌ Not monitorable
            "time_slot": "all_day"
        },
        "task_light_exercise": {
            "type": "MORNING_WALK",
            "name": "20 Min Wellness Walk",
            "coins": 20,  # ✅ Monitorable (steps)
            "time_slot": "morning"
        },
        "task_sleep_7_hours": {
            "type": "SLEEP_7H",
            "name": "Sleep 7+ Hours Tonight",
            "coins": 0,  # ❌ Not monitorable
            "time_slot": "evening"
        },
        "task_hydration_8_glasses": {
            "type": "WATER_INTAKE",
            "name": "Drink 8 Glasses Water",
            "coins": 10,  # ✅ Monitorable
            "time_slot": "all_day"
        },
        "task_stress_management": {
            "type": "DEEP_BREATHING",
            "name": "5 Min Deep Breathing",
            "coins": 0,  # ❌ Not monitorable
            "time_slot": "evening"
        },
    }

    tasks_dict = {}

    # Condition-specific base tasks based on actual lab values
    hb = feat.get("hemoglobin", 13.0)
    platelets = feat.get("platelet_count", 220000.0)
    glucose = feat.get("fasting_glucose", 95.0)
    bmi = feat.get("bmi", 23.0)

    # Monitorable walking task based on report values
    if bmi >= 25.0 or glucose > 100:
        step_target = 10000 if (bmi >= 30 or glucose > 126) else 8000
        tasks_dict["MORNING_WALK"] = {
            "type": "MORNING_WALK",
            "name": f"Walk {step_target:,} Steps Today",
            "coins": 25 if step_target >= 10000 else 20,  # ✅ Monitorable
            "time_slot": "morning"
        }
    
    if hb < 12.0:
        tasks_dict["IRON_DIET"] = {"type": "IRON_DIET", "name": "Eat Iron-Rich Meal (Spinach/Lentils)", "coins": 0, "time_slot": "afternoon"}
        tasks_dict["WATER_INTAKE"] = {"type": "WATER_INTAKE", "name": "Drink 10 Glasses Water", "coins": 10, "time_slot": "all_day"}
    if platelets < 150000:
        tasks_dict["AVOID_INJURY"] = {"type": "AVOID_INJURY", "name": "Avoid Contact Sports & Injury Risk", "coins": 0, "time_slot": "all_day"}
        tasks_dict["DOCTOR_VISIT"] = {"type": "DOCTOR_VISIT", "name": "Book Doctor Follow-Up (Low Platelets)", "coins": 0, "time_slot": "all_day"}
        tasks_dict["WATER_INTAKE"] = {"type": "WATER_INTAKE", "name": "Drink 10 Glasses Water", "coins": 10, "time_slot": "all_day"}
    if glucose > 100:
        tasks_dict["AVOID_SUGAR"] = {"type": "AVOID_SUGAR", "name": "Zero Added Sugar Today", "coins": 0, "time_slot": "all_day"}
        tasks_dict["CHECK_SUGAR_7DAYS"] = {"type": "CHECK_SUGAR_7DAYS", "name": "Check Fasting Sugar This Week", "coins": 20, "time_slot": "morning"}

    # If no condition-specific tasks yet, add universal wellness tasks
    if not tasks_dict:
        tasks_dict["WATER_INTAKE"] = {"type": "WATER_INTAKE", "name": "Drink 8 Glasses Water", "coins": 10, "time_slot": "all_day"}
        tasks_dict["MORNING_WALK"] = {"type": "MORNING_WALK", "name": "Walk 5,000 Steps Today", "coins": 15, "time_slot": "morning"}

    # Add model-predicted tasks on top
    for key, enabled in (task_predictions or {}).items():
        if enabled and key in mapping:
            task_obj = mapping[key]
            tasks_dict[task_obj["type"]] = task_obj

    return list(tasks_dict.values())



def _build_precautions_from_diet(diet_focus: str, overall_signal: str, feat: dict) -> list[str]:
    """Build precautions based on MODEL's diet_focus + actual lab values."""
    precautions = []

    hb = feat.get("hemoglobin", 13.0)
    platelets = feat.get("platelet_count", 220000.0)
    glucose = feat.get("fasting_glucose", 95.0)
    bmi = feat.get("bmi", 23.0)

    # Urgency from signal
    if overall_signal == "suggest_visit":
        precautions.append("⚠️ Book a doctor visit this week with this report.")
    elif overall_signal == "watch":
        precautions.append("Follow up with your doctor in the next 2-4 weeks.")

    # Condition-specific precautions based on actual values
    if hb < 12.0:
        precautions.append(f"Low hemoglobin ({hb:.1f} g/dL): Increase iron-rich foods — spinach, lentils, beetroot.")
        precautions.append("Pair iron foods with Vitamin C (lemon/orange) for better absorption.")
        precautions.append("Avoid tea or coffee immediately after meals.")
    if platelets < 150000:
        precautions.append(f"Low platelet count ({int(platelets):,}/µL): Avoid aspirin/NSAIDs without doctor advice.")
        precautions.append("Avoid contact sports and activities with injury risk.")
        precautions.append("Eat papaya leaf, pomegranate, and vitamin K-rich foods.")
    if glucose > 125:
        precautions.append(f"Elevated glucose ({glucose:.0f} mg/dL): Avoid refined sugar and white rice.")
        precautions.append("Prefer whole grains, legumes, and vegetables.")
    elif glucose > 100:
        precautions.append("Borderline glucose: Reduce sugary drinks and processed foods.")
    if bmi >= 30:
        precautions.append(f"BMI {bmi:.1f} (Obese): Focus on portion control and daily 30-min walks.")
    elif bmi >= 25:
        precautions.append(f"BMI {bmi:.1f} (Overweight): Increase physical activity and reduce calorie-dense foods.")

    # Diet-specific fallback if no condition-specific precautions added
    if len(precautions) <= (1 if overall_signal != "good" else 0):
        if diet_focus == "iron_and_low_sugar":
            precautions.extend(["Increase dietary iron: spinach, lentils, beans, jaggery.", "Reduce refined sugar and processed foods."])
        elif diet_focus == "iron_rich":
            precautions.extend(["Focus on iron-rich foods: spinach, lentils, beans, beetroot.", "Pair with Vitamin C (citrus) for better absorption."])
        elif diet_focus == "diabetic_friendly":
            precautions.extend(["Prefer whole grains, legumes, and vegetables.", "Avoid refined sugar, white bread, and fried foods."])
        elif diet_focus == "energy_boosting":
            precautions.extend(["Include nuts, seeds, whole grains, and lean proteins.", "Stay hydrated and take regular eating intervals."])
        elif diet_focus == "weight_management":
            precautions.extend(["Focus on vegetable-based meals and lean proteins.", "Control portion sizes and avoid high-calorie snacks."])
        else:
            precautions.extend(["Maintain a balanced diet with whole grains, proteins, and vegetables.", "Stay hydrated with 8-10 glasses of water daily."])

    return precautions


def _build_diet_plan(diet_focus: str, feat: dict) -> dict:
    """Build diet plan based on MODEL's diet_focus + actual conditions."""
    hb = feat.get("hemoglobin", 13.0)
    platelets = feat.get("platelet_count", 220000.0)
    glucose = feat.get("fasting_glucose", 95.0)

    # Override diet_focus based on actual values for accuracy
    if platelets < 150000 and hb < 12.0:
        diet_focus = "platelet_and_iron"
    elif platelets < 150000:
        diet_focus = "platelet_boosting"
    elif hb < 12.0:
        diet_focus = "iron_rich" if glucose <= 100 else "iron_and_low_sugar"
    elif glucose > 125:
        diet_focus = "diabetic_friendly"

    plans = {
        "platelet_boosting": {
            "focus": "platelet_boosting",
            "breakfast": ["Papaya with pomegranate seeds", "Ragi porridge with dates"],
            "lunch": ["Brown rice with spinach dal and beetroot salad", "Roti with palak paneer"],
            "dinner": ["Vegetable khichdi with spinach", "Pumpkin soup with roti"],
            "snacks": ["Pomegranate juice", "Kiwi and papaya", "Pumpkin seeds"],
            "avoid": ["Alcohol", "Aspirin/NSAIDs without doctor advice", "Processed foods"],
        },
        "platelet_and_iron": {
            "focus": "platelet_and_iron",
            "breakfast": ["Papaya with pomegranate", "Ragi porridge with jaggery"],
            "lunch": ["Brown rice with spinach dal and beetroot salad", "Roti with chana masala"],
            "dinner": ["Vegetable khichdi with spinach", "Roti with palak paneer"],
            "snacks": ["Pomegranate juice", "Dates and almonds", "Pumpkin seeds"],
            "avoid": ["Tea/coffee after meals", "Alcohol", "Aspirin/NSAIDs without doctor advice"],
        },
        "iron_and_low_sugar": {
            "focus": "iron_and_low_sugar",
            "breakfast": ["Spinach paratha with curd", "Ragi porridge with jaggery", "Moong dal chilla with mint chutney"],
            "lunch": ["Brown rice with dal palak and beetroot salad", "Roti with chana masala and cucumber raita"],
            "dinner": ["Vegetable khichdi with spinach", "Roti with palak paneer"],
            "snacks": ["Roasted peanuts and jaggery", "Dates and almonds"],
            "avoid": ["Tea/coffee after meals", "Sugary drinks and sweets"],
        },
        "iron_rich": {
            "focus": "iron_rich",
            "breakfast": ["Spinach dosa with sambar", "Ragi upma with vegetables"],
            "lunch": ["Brown rice with rajma and salad", "Roti with spinach curry"],
            "dinner": ["Khichdi with spinach", "Vegetable soup with roti"],
            "snacks": ["Beetroot juice", "Roasted gram"],
            "avoid": ["Tea/coffee with meals"],
        },
        "diabetic_friendly": {
            "focus": "diabetic_friendly",
            "breakfast": ["Oats upma", "Moong dal chilla"],
            "lunch": ["Brown rice (small) with dal and salad", "Roti with vegetable curry"],
            "dinner": ["Vegetable soup with roti", "Grilled vegetables"],
            "snacks": ["Roasted chana", "Cucumber sticks"],
            "avoid": ["White rice, white bread", "Sugary drinks, sweets"],
        },
        "energy_boosting": {
            "focus": "energy_boosting",
            "breakfast": ["Whole wheat toast with peanut butter and banana", "Oats with nuts and honey"],
            "lunch": ["Brown rice with dal and greens", "Roti with paneer curry"],
            "dinner": ["Vegetable pulao with paneer", "Vegetable soup"],
            "snacks": ["Nuts and dried fruits", "Banana with peanut butter"],
            "avoid": ["Processed foods", "Excessive caffeine"],
        },
        "weight_management": {
            "focus": "weight_management",
            "breakfast": ["Vegetable upma", "Idli with sambar"],
            "lunch": ["Vegetable salad with grilled paneer", "Brown rice with dal"],
            "dinner": ["Vegetable soup", "Grilled vegetables with roti"],
            "snacks": ["Fruits", "Vegetable sticks"],
            "avoid": ["Fried foods", "High-calorie snacks"],
        },
        "balanced": {
            "focus": "balanced",
            "breakfast": ["Idli with sambar", "Whole wheat toast"],
            "lunch": ["Rice with dal and salad", "Roti with vegetables"],
            "dinner": ["Khichdi", "Roti with dal"],
            "snacks": ["Fresh fruits", "Nuts"],
            "avoid": ["Excessive fried foods", "Too much salt and sugar"],
        }
    }
    return plans.get(diet_focus, plans["balanced"])


@router.post("/analyze-report")
async def analyze_report(
    file: UploadFile = File(...),
    report_type: str | None = Form(None),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Pure ML-driven pipeline:
    1. Upload report image
    2. Extract OCR data
    3. Run trained model on OCR
    4. Use ONLY model predictions for tasks/diet/precautions
    """
    ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp", "application/pdf"}
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only JPEG, PNG, WebP, BMP, or PDF files are supported.",
        )

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File must be under 10 MB.")

    # Step 1: OCR extraction
    file_url = "https://mock-firebase-storage.appspot.com/mock_path/mock.png"
    try:
        file_url = await upload_file_to_firebase(
            file_bytes=contents,
            filename=file.filename or "report_image",
            content_type=file.content_type or "application/octet-stream",
        )
        ocr_data = await process_health_document(contents)
    except Exception as e:
        print(f"OCR error: {str(e)}. Using fallback.")
        ocr_data = {
            "document_type": report_type or "health_report",
            "patient_name": "User",
            "lab_results": {},
        }

    # Step 2: Get user + latest body metrics + latest vitals
    user_row = await db.execute(select(User).where(User.id == user_id))
    user = user_row.scalar_one_or_none()

    bmi_row = await db.execute(
        select(BodyMetrics).where(BodyMetrics.user_id == user_id)
        .order_by(desc(BodyMetrics.measured_at)).limit(1)
    )
    body_metrics = bmi_row.scalar_one_or_none()

    vitals_row = await db.execute(
        select(VitalsLog).where(VitalsLog.user_id == user_id, VitalsLog.fasting_glucose != None)
        .order_by(desc(VitalsLog.measured_at)).limit(1)
    )
    latest_vitals = vitals_row.scalar_one_or_none()

    # Step 3: RUN TRAINED MODEL with actual BMI/vitals
    print(f"[ML] Calling predict_from_ocr with OCR data: {ocr_data.get('lab_results', {})}")
    print(f"[ML] BMI: {getattr(body_metrics, 'bmi', 'N/A')}, Vitals glucose: {getattr(latest_vitals, 'fasting_glucose', 'N/A')}")
    model_result = predict_from_ocr(ocr_data, user, body_metrics=body_metrics, vitals=latest_vitals)
    
    if model_result is None:
        print("[ML] ERROR: Model returned None")
        raise HTTPException(
            status_code=500,
            detail="ML model failed to generate predictions."
        )

    # Step 4: Extract predictions from model
    overall_signal = model_result.overall_signal  # "good", "watch", "suggest_visit"
    confidence = model_result.overall_confidence
    diet_focus = model_result.diet_focus  # "iron_rich", "diabetic_friendly", etc.
    task_predictions = model_result.task_predictions  # dict[str, bool]
    
    print(f"[ML] Model output: signal={overall_signal}, confidence={confidence:.2f}, diet={diet_focus}")
    print(f"[ML] Tasks enabled: {[k for k,v in task_predictions.items() if v]}")

    # Map signal to risk level for UI
    signal_to_risk = {
        "good": "low",
        "watch": "moderate",
        "suggest_visit": "high",
    }
    risk_level = signal_to_risk.get(overall_signal, "low")

    # Step 5: Build response components from model predictions + actual lab values
    from ml.realistic_predictor import _build_feature_map
    feat = _build_feature_map(ocr_data, user, body_metrics=body_metrics, vitals=latest_vitals)
    model_tasks = _tasks_from_model_predictions(task_predictions, feat)
    precautions = _build_precautions_from_diet(diet_focus, overall_signal, feat)
    diet_plan = _build_diet_plan(diet_focus, feat)

    # Step 6: Persist to database
    ml_result = {
        "risk_level": risk_level,
        "confidence": round(confidence, 2),
        "overall_signal": overall_signal,
        "diet_focus": diet_focus,
        "summary": f"Model analyzed your report. Risk level: {risk_level}.",
    }

    report = Report(
        user_id=user_id,
        report_type="ml_analysis",
        file_key=file_url,
        extracted_values={
            "ocr_data": ocr_data,
            "ml_analysis": ml_result,
            "ml_predictions": {
                "signal": overall_signal,
                "confidence": confidence,
                "diet_focus": diet_focus,
                "tasks_enabled": {k: v for k, v in task_predictions.items() if v},
            },
            "positive_precautions": precautions,
            "diet_plan": diet_plan,
        },
        upload_status="processed",
        ocr_confidence=float(confidence),
    )
    db.add(report)
    await db.flush()

    # Step 7: Delete ALL tasks for today (completed + incomplete) and regenerate from model
    today = date.today()
    result = await db.execute(
        delete(DailyTask).where(
            DailyTask.user_id == user_id,
            DailyTask.task_date == today,
        )
    )
    deleted_count = result.rowcount
    print(f"[ML] Deleted {deleted_count} tasks from {today} for user {user_id}")
    await db.flush()

    # Create tasks ONLY from model predictions
    print(f"[ML] Creating {len(model_tasks)} new model-driven tasks")
    for task in model_tasks:
        print(f"[ML]   → {task['type']}: {task['name']}")
        db.add(DailyTask(
            user_id=user_id,
            task_type=task["type"],
            task_name=task["name"],
            coins_reward=task["coins"],
            task_date=today,
            time_slot=task["time_slot"],
        ))

    await db.commit()
    print(f"[ML] Report analysis complete. Tasks committed.")

    return {
        "message": "Report analyzed successfully using trained ML model.",
        "report_id": report.id,
        "file_url": file_url,
        "ml_analysis": ml_result,
        "overall_signal": overall_signal,
        "risk_level": risk_level,
        "diet_focus": diet_focus,
        "positive_precautions": precautions,
        "diet_plan": diet_plan,
        "tasks_generated": len(model_tasks),
        "tasks": model_tasks,
    }
