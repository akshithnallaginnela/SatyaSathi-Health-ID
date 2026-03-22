"""
ML Router — analyze uploaded health reports using OCR + rule-based risk classifier.
POST /api/ml/analyze-report
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from security.jwt_handler import get_current_user_id
from services.ocr_service import process_health_document
from services.storage_service import upload_file_to_firebase
from models.report import Report
from ml.report_analyzer import analyze

router = APIRouter(prefix="/api/ml", tags=["ML Analysis"])


@router.post("/analyze-report")
async def analyze_report(
    file: UploadFile = File(...),
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

    # Step 3: Persist report + extracted values for history APIs
    report_type = str(ocr_data.get("document_type") or "health_report").lower().replace(" ", "_")
    report = Report(
        user_id=user_id,
        report_type=report_type,
        file_key=file_url,
        extracted_values={
            "ocr_data": ocr_data,
            "ml_analysis": ml_result,
            "original_filename": file.filename,
        },
        upload_status="processed",
        ocr_confidence=float(ml_result.get("confidence", 0.0)),
    )
    db.add(report)
    await db.flush()

    return {
        "message": "Report analyzed successfully.",
        "report_id": report.id,
        "file_url": file_url,
        "ocr_data": ocr_data,
        "ml_analysis": ml_result,
    }
