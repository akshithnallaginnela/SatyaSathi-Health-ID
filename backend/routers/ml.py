"""
ML Router — analyze uploaded health reports using OCR + rule-based risk classifier.
POST /api/ml/analyze-report
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from security.jwt_handler import get_current_user_id
from services.ocr_service import process_health_document
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

    return {
        "message": "Report analyzed successfully.",
        "ocr_data": ocr_data,
        "ml_analysis": ml_result,
    }
