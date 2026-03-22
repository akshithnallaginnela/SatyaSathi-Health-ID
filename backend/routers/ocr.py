from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from services.ocr_service import process_health_document
from services.storage_service import upload_file_to_firebase
from services.blockchain_service import mint_health_record
from security.jwt_handler import get_current_user_id
from database import get_db
from models.report import Report

router = APIRouter(prefix="/api/ocr", tags=["OCR & Document Processing"])


def _parse_report_date(value: str | None):
    if not value:
        return None
    # OCR date format can vary; only persist when it is parseable.
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None

@router.post("/analyze")
async def analyze_document(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload an image of a medical document (prescription, report, etc.)
    and extract structured medical data using Gemini 1.5 Flash.
    """
    # Validate file type
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/bmp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail="Invalid file format. Please upload a JPEG, PNG, WEBP, or BMP image."
        )
        
    try:
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File must be under 10 MB.")

        safe_filename = file.filename or "report_image"
        safe_content_type = file.content_type or "application/octet-stream"
        
        # 1. Upload the raw image/PDF file to Firebase Storage
        file_url = await upload_file_to_firebase(
            file_bytes=contents, 
            filename=safe_filename,
            content_type=safe_content_type
        )
        # 2. Extract structured medical data using Gemini Fast Vision
        extracted_data = await process_health_document(contents)

        # 3. Persist report row for reports/history APIs
        report_type = str(extracted_data.get("document_type") or "health_report").lower().replace(" ", "_")
        report = Report(
            user_id=user_id,
            report_type=report_type,
            file_key=file_url,
            extracted_values=extracted_data,
            upload_status="processed",
            ocr_confidence=1.0,
            report_date=_parse_report_date(extracted_data.get("date")),
        )
        db.add(report)
        await db.flush()
        
        # 4. Mint an immutable record of the medical report on Polygon Blockchain
        tx_hash = await mint_health_record(user_id, file_url, extracted_data)
        
        return {
            "success": True,
            "report_id": report.id,
            "upload_status": report.upload_status,
            "filename": safe_filename,
            "file_url": file_url,
            "tx_hash": tx_hash,
            "data": extracted_data
        }
    except ValueError as val_err:
        raise HTTPException(status_code=500, detail=str(val_err))
    except Exception as e:
        print(f"OCR Router Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process document through OCR engine.")
