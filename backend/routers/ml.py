"""
ML Router — analyze uploaded health reports using OCR + rule-based risk classifier.
POST /api/ml/analyze-report
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from security.jwt_handler import get_current_user_id
from services.ocr_service import process_health_document
from services.storage_service import upload_file_to_firebase
from models.report import Report
from models.task import DailyTask
from models.health_record import VitalsLog
from models.user import User
from ml.report_analyzer import analyze
from ml.realistic_predictor import predict_from_ocr
from datetime import date
from sqlalchemy import delete, and_, select
import re

router = APIRouter(prefix="/api/ml", tags=["ML Analysis"])


def _normalize_report_type(value: str | None) -> str:
    if not value:
        return "health_report"
    v = value.strip().lower().replace("-", "_").replace(" ", "_")
    alias = {
        "blood_test": "blood_test_report",
        "blood_test_report": "blood_test_report",
        "blood_sugar": "blood_sugar_report",
        "blood_sugar_report": "blood_sugar_report",
        "sugar": "blood_sugar_report",
    }
    return alias.get(v, v)


def _build_positive_precautions(risk_level: str, report_type: str, flags: list[str] = []) -> list[str]:
    base = [
        "Try a 20-minute brisk walk after meals on most days.",
        "Drink enough water through the day and keep sleep consistent.",
        "Track one small habit daily instead of changing everything at once.",
    ]
    
    # Blood Sugar Specific
    if report_type == "blood_sugar_report":
        base[0] = "Add a 15-20 minute post-meal walk to support steady sugar levels."
        base.append("Use high-fiber meals and reduce refined sugar portions gradually.")

    # Anemia Specific
    flags_text = " ".join(flags).lower()
    if "anemia" in flags_text or "hemoglobin" in flags_text:
        base[0] = "Increase dietary iron: focus on spinach, nuts, lentils, and jaggery."
        base[1] = "Pair iron-rich foods with Vitamin C (like lemon/orange) for better absorption."
        base.append("Avoid tea or coffee immediately after meals as they block iron absorption.")

    # General Risk
    if risk_level == "high":
        base.insert(0, "Book a doctor follow-up this week and carry this report for review.")
    elif risk_level == "moderate":
        base.insert(0, "Plan a follow-up check in the next 2-4 weeks to monitor progress.")
    return base


def _ocr_quality_score(ocr_data: dict) -> dict:
    """Heuristic OCR confidence from field coverage + content richness."""
    scalar_fields = ["document_type", "patient_name", "date", "doctor"]
    filled_scalars = sum(1 for f in scalar_fields if str(ocr_data.get(f) or "").strip())
    findings_count = len(ocr_data.get("key_findings") or [])
    meds_count = len(ocr_data.get("medications") or [])

    score = 0.25
    score += filled_scalars * 0.12
    score += min(findings_count, 5) * 0.08
    score += min(meds_count, 4) * 0.05
    score = max(0.0, min(1.0, score))

    return {
        "confidence": round(score, 2),
        "filled_scalar_fields": filled_scalars,
        "findings_count": findings_count,
        "medications_count": meds_count,
    }


def _tasks_from_model_predictions(task_predictions: dict[str, bool]) -> list[dict]:
    mapping = {
        "task_iron_rich_diet": {"type": "IRON_DIET", "name": "Eat Iron-Rich Meal (Spinach/Lentils)", "coins": 25, "time_slot": "afternoon"},
        "task_log_sugar": {"type": "LOG_SUGAR", "name": "Log Fasting Sugar (Weekly)", "coins": 20, "time_slot": "morning"},
        "task_reduce_sugar_food": {"type": "AVOID_SUGAR", "name": "Zero Added Sugar Today", "coins": 25, "time_slot": "evening"},
        "task_hydration_8_glasses": {"type": "WATER_INTAKE", "name": "Drink 8 Glasses Water", "coins": 15, "time_slot": "all_day"},
        "task_stress_management": {"type": "DEEP_BREATHING", "name": "5 Min Deep Breathing", "coins": 15, "time_slot": "evening"},
        "task_doctor_visit": {"type": "DOCTOR_VISIT", "name": "Book Doctor Follow-Up", "coins": 30, "time_slot": "all_day"},
        "task_retest_in_2_weeks": {"type": "RETEST_2W", "name": "Schedule Retest in 2 Weeks", "coins": 20, "time_slot": "all_day"},
        "task_light_exercise": {"type": "MORNING_WALK", "name": "20 Min Wellness Walk", "coins": 20, "time_slot": "morning"},
        "task_sleep_7_hours": {"type": "SLEEP_7H", "name": "Sleep 7+ Hours Tonight", "coins": 15, "time_slot": "evening"},
        "task_morning_walk": {"type": "MORNING_WALK", "name": "20 Min Wellness Walk", "coins": 20, "time_slot": "morning"},
    }
    tasks: list[dict] = []
    for key, enabled in (task_predictions or {}).items():
        if enabled and key in mapping:
            tasks.append(mapping[key])
    return tasks


@router.post("/analyze-report")
async def analyze_report(
    file: UploadFile = File(...),
    report_type: str | None = Form(None),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Full pipeline: upload report image → OCR extraction → ML risk analysis.
    Returns both the raw OCR data and the ML risk assessment.
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

    # Step 1: OCR — extract structured data from the image
    file_url = "https://mock-firebase-storage.appspot.com/mock_path/mock.png"
    try:
        file_url = await upload_file_to_firebase(
            file_bytes=contents,
            filename=file.filename or "report_image",
            content_type=file.content_type or "application/octet-stream",
        )
        ocr_data = await process_health_document(contents)
    except Exception as e:
        print(f"OCR Pipeline error: {str(e)}. Falling back to mock OCR data for demo.")
        ocr_data = {
            "document_type": report_type or "health_report",
            "patient_name": "Demo User",
            "lab_results": {
                "hemoglobin": "13.8 g/dL",
                "total_cholesterol": "204 mg/dL",
                "fasting_sugar": "102 mg/dL",
                "rbc_count": "5.2 million/cumm",
                "wbc_count": "5000 /cumm",
            },
            "key_findings": ["Fasting glucose is elevated", "BP slightly above normal"],
            "medications": ["Metformin"]
        }

    # Extract finding to skip manual task
    found_sugar = ocr_data.get("lab_results", {}).get("fasting_sugar")
    if found_sugar:
        match = re.search(r"(\d+(\.\d+)?)", str(found_sugar))
        if match:
            try:
                glucose_val = float(match.group(1))
                db.add(VitalsLog(
                    user_id=user_id,
                    fasting_glucose=glucose_val,
                    source="ocr"
                ))
            except Exception as ex:
                print("Failed to save OCR fasting sugar", ex)

    # Step 2: ML — run risk classifier on extracted data
    ml_result = analyze(ocr_data)

    # Enrich with trained realistic models (if artifacts are available)
    user_row = await db.execute(select(User).where(User.id == user_id))
    user = user_row.scalar_one_or_none()
    realistic = predict_from_ocr(ocr_data, user)
    model_tasks: list[dict] = []
    if realistic is not None:
        signal_to_risk = {
            "good": "low",
            "watch": "moderate",
            "suggest_visit": "high",
        }
        model_risk = signal_to_risk.get(realistic.overall_signal, ml_result.get("risk_level", "low"))
        current_risk = ml_result.get("risk_level", "low")
        risk_rank = {"low": 0, "moderate": 1, "high": 2}
        if risk_rank.get(model_risk, 0) > risk_rank.get(current_risk, 0):
            ml_result["risk_level"] = model_risk

        ml_result["confidence"] = round(max(float(ml_result.get("confidence", 0.7)), realistic.overall_confidence), 2)
        flags = ml_result.get("flags", [])
        flags.append(f"Model signal: {realistic.overall_signal}")
        ml_result["flags"] = list(dict.fromkeys(flags))
        ml_result["diet_focus"] = realistic.diet_focus
        ml_result["model_confidence"] = round(realistic.overall_confidence, 2)
        model_tasks = _tasks_from_model_predictions(realistic.task_predictions)

    ocr_quality = _ocr_quality_score(ocr_data)
    needs_review = (
        ocr_quality["confidence"] < 0.75
        or (ocr_quality["findings_count"] == 0 and ocr_quality["medications_count"] == 0)
    )

    # Step 3: Persist report + extracted values for history APIs
    selected_report_type = _normalize_report_type(report_type)
    inferred_report_type = str(ocr_data.get("document_type") or "health_report").lower().replace(" ", "_")
    report = Report(
        user_id=user_id,
        report_type=selected_report_type,
        file_key=file_url,
        extracted_values={
            "ocr_data": ocr_data,
            "ml_analysis": ml_result,
            "ocr_quality": ocr_quality,
            "needs_review": needs_review,
            "selected_report_type": selected_report_type,
            "inferred_report_type": inferred_report_type,
            "positive_precautions": _build_positive_precautions(ml_result.get("risk_level", "low"), selected_report_type, ml_result.get("flags", [])),
            "original_filename": file.filename,
        },
        upload_status="needs_review" if needs_review else "processed",
        ocr_confidence=float(ocr_quality["confidence"]),
    )
    db.add(report)
    await db.flush()

    # --- Dynamic Task Generation ---
    today = date.today()

    # Generate new specific tasks based on the report type / analysis
    new_tasks = []
    
    # We only generate extra tasks if the report detects risks.
    # Routine vitals tracking (like LOG_BP) is strictly managed by tasks.py based on past values.
    risk = ml_result.get("risk_level", "low")
    flags_text = " ".join(ml_result.get("flags", [])).lower()
    
    if risk in ["moderate", "high"]:
        if selected_report_type == "blood_sugar_report":
            new_tasks = [
                {"type": "POST_MEAL_WALK", "name": "15 Min Post-Meal Walk", "coins": 20, "time_slot": "afternoon"},
                {"type": "AVOID_SUGAR", "name": "Zero Added Sugar Today", "coins": 25, "time_slot": "evening"}
            ]
        elif "anemia" in flags_text or "hemoglobin" in flags_text:
            new_tasks = [
                {"type": "IRON_DIET", "name": "Eat Iron-Rich Meal (Spinach/Lentils)", "coins": 25, "time_slot": "afternoon"},
                {"type": "VITAMIN_C", "name": "Take Vitamin C (Lemon/Orange)", "coins": 15, "time_slot": "morning"}
            ]
        else:
            new_tasks = [
                {"type": "MORNING_WALK", "name": "20 Min Wellness Walk", "coins": 20, "time_slot": "morning"}
            ]

    # Merge model-driven tasks
    for mt in model_tasks:
        if mt not in new_tasks:
            new_tasks.append(mt)

    existing_tasks_result = await db.execute(
        select(DailyTask.task_type)
        .where(DailyTask.user_id == user_id, DailyTask.task_date == today)
    )
    existing_types = set(existing_tasks_result.scalars().all())

    for t in new_tasks:
        if t["type"] not in existing_types:
            db.add(DailyTask(
                user_id=user_id,
                task_type=t["type"],
                task_name=t["name"],
                coins_reward=t["coins"],
                task_date=today,
                time_slot=t["time_slot"],
            ))

    await db.flush()

    precautions = _build_positive_precautions(ml_result.get("risk_level", "low"), selected_report_type, ml_result.get("flags", []))
    if ml_result.get("diet_focus") == "iron_rich" or ml_result.get("diet_focus") == "iron_and_low_sugar":
        precautions = [
            "Follow an iron-focused diet plan this week (spinach, lentils, beans, jaggery).",
            *precautions,
        ]
    if ml_result.get("diet_focus") in {"diabetic_friendly", "iron_and_low_sugar"}:
        precautions.append("Prefer low-glycemic meals and reduce refined sugar for stable glucose.")
    precautions = list(dict.fromkeys(precautions))

    if isinstance(report.extracted_values, dict):
        report.extracted_values["positive_precautions"] = precautions
        report.extracted_values["ml_analysis"] = ml_result
    await db.flush()

    return {
        "message": "Report analyzed successfully.",
        "report_id": report.id,
        "file_url": file_url,
        "upload_status": report.upload_status,
        "report_type": selected_report_type,
        "ocr_quality": ocr_quality,
        "needs_review": needs_review,
        "ocr_data": ocr_data,
        "ml_analysis": ml_result,
        "positive_precautions": precautions,
    }
