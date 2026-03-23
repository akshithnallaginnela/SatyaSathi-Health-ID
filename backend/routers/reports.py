import os
import shutil
import uuid
import datetime
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from database import get_db
from models.domain import (
    BloodReport, UserDataStatus, User
)
from security.jwt_handler import get_current_user_id
from services.ocr_service import extract_report_values
from ml.analysis_engine import run_full_analysis

router = APIRouter(prefix="/api/reports", tags=["Reports"])

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/analyze")
async def analyze_report(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    1. Upload file
    2. Run Gemini OCR
    3. Save to BloodReport
    4. Trigger preventive analysis
    """
    # 1. Basic file validation
    if file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ["jpg", "jpeg", "png", "pdf"]:
        raise HTTPException(status_code=400, detail="Unsupported file format")

    # 2. Save file
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.{file_ext}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 3. Run Gemini OCR
    try:
        extracted = await extract_report_values(file_path)
    except Exception as e:
        print(f"OCR Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze report via Gemini.")

    # 4. Save to DB
    report = BloodReport(
        user_id=user_id,
        file_path=file_path,
        lab_name=extracted.get("lab_name"),
        report_date=datetime.date.today(), # Or parse from extracted["report_date"]
        
        hemoglobin=extracted.get("hemoglobin"),
        rbc_count=extracted.get("rbc_count"),
        pcv=extracted.get("pcv"),
        mcv=extracted.get("mcv"),
        mch=extracted.get("mch"),
        mchc=extracted.get("mchc"),
        rdw=extracted.get("rdw"),
        wbc_count=extracted.get("wbc_count"),
        neutrophils_pct=extracted.get("neutrophils_pct"),
        lymphocytes_pct=extracted.get("lymphocytes_pct"),
        monocytes_pct=extracted.get("monocytes_pct"),
        eosinophils_pct=extracted.get("eosinophils_pct"),
        basophils_pct=extracted.get("basophils_pct"),
        platelet_count=extracted.get("platelet_count"),
        fasting_glucose=extracted.get("fasting_glucose"),
        random_glucose=extracted.get("random_glucose"),
        urea=extracted.get("urea"),
        creatinine=extracted.get("creatinine"),
        
        lab_interpretation=extracted.get("lab_interpretation"),
        ocr_raw=json.dumps(extracted) # Simplified raw store
    )
    db.add(report)
    
    # 5. Update Status
    result = await db.execute(select(UserDataStatus).where(UserDataStatus.user_id == user_id))
    status = result.scalar_one_or_none()
    if status:
        status.has_report = True
        status.report_count += 1
    
    await db.flush()

    # 6. Trigger Full ML Analysis
    analysis = await run_full_analysis(user_id, db)
    
    return {
        "message": "Report analyzed successfully",
        "extracted_values": extracted,
        "preventive_care": analysis["preventive_care"],
        "tasks_generated": analysis["tasks"],
        "diet_plan": analysis["diet"]
    }

@router.get("/")
async def list_reports(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BloodReport)
        .where(BloodReport.user_id == user_id)
        .order_by(desc(BloodReport.uploaded_at))
    )
    return result.scalars().all()
