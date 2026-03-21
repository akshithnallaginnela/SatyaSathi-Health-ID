from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict
from services.ocr_service import process_health_document
from services.storage_service import upload_file_to_firebase
from services.blockchain_service import mint_health_record

router = APIRouter(prefix="/api/ocr", tags=["OCR & Document Processing"])

@router.post("/analyze")
async def analyze_document(file: UploadFile = File(...)):
    """
    Upload an image of a medical document (prescription, report, etc.)
    and extract structured medical data using Gemini 1.5 Flash.
    """
    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(
            status_code=400, 
            detail="Invalid file format. Please upload a JPEG, PNG, or WEBP image."
        )
        
    try:
        contents = await file.read()
        
        # 1. Upload the raw image/PDF file to Firebase Storage
        file_url = await upload_file_to_firebase(
            file_bytes=contents, 
            filename=file.filename,
            content_type=file.content_type
        )
        # 2. Extract structured medical data using Gemini Fast Vision
        extracted_data = await process_health_document(contents)
        
        # 3. Mint an immutable record of the medical report on Polygon Blockchain
        # (Using a mock patient ID for demo, in reality we'd extract user_id from JWT token payload)
        tx_hash = await mint_health_record("PATIENT-ID-DEMO", file_url, extracted_data)
        
        return {
            "success": True,
            "filename": file.filename,
            "file_url": file_url,
            "tx_hash": tx_hash,
            "data": extracted_data
        }
    except ValueError as val_err:
        raise HTTPException(status_code=500, detail=str(val_err))
    except Exception as e:
        print(f"OCR Router Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process document through OCR engine.")
