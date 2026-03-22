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
from ml.report_analyzer import analyze
from datetime import date
from sqlalchemy import delete, and_

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


def _build_positive_precautions(risk_level: str, report_type: str) -> list[str]:
    base = [
        "Try a 20-minute brisk walk after meals on most days.",
        "Drink enough water through the day and keep sleep consistent.",
        "Track one small habit daily instead of changing everything at once.",
    ]
    if report_type == "blood_sugar_report":
        base[0] = "Add a 15-20 minute post-meal walk to support steady sugar levels."
        base.append("Use high-fiber meals and reduce refined sugar portions gradually.")
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
    ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp"}
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only JPEG, PNG, WebP, or BMP images are supported for ML analysis.",
        )

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File must be under 10 MB.")

    # Step 1: OCR — extract structured data from the image
    try:
        file_url = await upload_file_to_firebase(
            file_bytes=contents,
            filename=file.filename or "report_image",
            content_type=file.content_type or "application/octet-stream",
        )
        ocr_data = await process_health_document(contents)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Could not extract data from image: {str(e)}",
        )

    # Step 2: ML — run risk classifier on extracted data
    ml_result = analyze(ocr_data)
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
            "positive_precautions": _build_positive_precautions(ml_result.get("risk_level", "low"), selected_report_type),
            "original_filename": file.filename,
        },
        upload_status="needs_review" if needs_review else "processed",
        ocr_confidence=float(ocr_quality["confidence"]),
    )
    db.add(report)
    await db.flush()

    # --- Dynamic Task Generation ---
    today = date.today()
    # Delete previous dynamic tasks for today that haven't been completed yet
    default_types = ["DIET_MEAL", "WATER_INTAKE", "DEEP_BREATHING"]
    await db.execute(
        delete(DailyTask)
        .where(
            and_(
                DailyTask.user_id == user_id,
                DailyTask.task_date == today,
                DailyTask.completed == False,
                DailyTask.task_type.notin_(default_types)
            )
        )
    )

    # Generate new specific tasks based on the report type / analysis
    new_tasks = []
    if selected_report_type == "blood_sugar_report":
        new_tasks = [
            {"type": "POST_MEAL_WALK", "name": "15 Min Post-Meal Walk", "coins": 20, "time_slot": "afternoon"},
            {"type": "AVOID_SUGAR", "name": "Zero Added Sugar Today", "coins": 25, "time_slot": "evening"}
        ]
    else:
        new_tasks = [
            {"type": "LOG_BP", "name": "Log Morning BP", "coins": 15, "time_slot": "morning"},
            {"type": "MORNING_WALK", "name": "20 Min Morning Walk", "coins": 20, "time_slot": "morning"}
        ]

    for t in new_tasks:
        db.add(DailyTask(
            user_id=user_id,
            task_type=t["type"],
            task_name=t["name"],
            coins_reward=t["coins"],
            task_date=today,
            time_slot=t["time_slot"],
        ))

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
        "positive_precautions": _build_positive_precautions(ml_result.get("risk_level", "low"), selected_report_type),
    }
