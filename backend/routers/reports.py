import os
import shutil
import uuid
import datetime
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from database import get_db, async_session
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
        if not extracted:
            raise ValueError("Gemini returned empty result")
        
        # Log every extracted value
        print(f"\n{'='*50}")
        print(f"📋 OCR EXTRACTION RESULTS:")
        for key, val in extracted.items():
            if val is not None:
                print(f"   ✅ {key}: {val}")
        
        # Count how many actual health values were extracted
        health_keys = ["hemoglobin", "rbc_count", "wbc_count", "platelet_count", 
                       "fasting_glucose", "random_glucose", "creatinine", "urea"]
        extracted_count = sum(1 for k in health_keys if extracted.get(k) is not None)
        print(f"   📊 Extracted {extracted_count} health values out of {len(health_keys)}")
        print(f"{'='*50}\n")
        
    except Exception as e:
        print(f"❌ Gemini OCR ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        # Fallback empty result so we don't 500
        extracted = {"lab_name": "Extraction Failed", "message": f"Could not extract details: {str(e)}"}

    # 4. Save to DB
    report = BloodReport(
        user_id=user_id,
        file_path=file_path,
        lab_name=extracted.get("lab_name"),
        report_date=datetime.date.today(),
        hemoglobin=extracted.get("hemoglobin"),
        rbc_count=extracted.get("rbc_count"),
        pcv=extracted.get("pcv"),
        mcv=extracted.get("mcv"),
        mch=extracted.get("mch"),
        mchc=extracted.get("mchc"),
        rdw=extracted.get("rdw"),
        rdw_sd=extracted.get("rdw_sd"),
        mpv=extracted.get("mpv"),
        wbc_count=extracted.get("wbc_count"),
        neutrophils_pct=extracted.get("neutrophils_pct"),
        lymphocytes_pct=extracted.get("lymphocytes_pct"),
        monocytes_pct=extracted.get("monocytes_pct"),
        eosinophils_pct=extracted.get("eosinophils_pct"),
        basophils_pct=extracted.get("basophils_pct"),
        neutrophils_abs=extracted.get("neutrophils_abs"),
        lymphocytes_abs=extracted.get("lymphocytes_abs"),
        monocytes_abs=extracted.get("monocytes_abs"),
        eosinophils_abs=extracted.get("eosinophils_abs"),
        platelet_count=extracted.get("platelet_count"),
        p_lcr=extracted.get("p_lcr"),
        fasting_glucose=extracted.get("fasting_glucose"),
        random_glucose=extracted.get("random_glucose"),
        hba1c=extracted.get("hba1c"),
        urea=extracted.get("urea"),
        creatinine=extracted.get("creatinine"),
        uric_acid=extracted.get("uric_acid"),
        egfr=extracted.get("egfr"),
        sgpt=extracted.get("sgpt"),
        sgot=extracted.get("sgot"),
        bilirubin_total=extracted.get("bilirubin_total"),
        bilirubin_direct=extracted.get("bilirubin_direct"),
        alkaline_phosphatase=extracted.get("alkaline_phosphatase"),
        albumin=extracted.get("albumin"),
        total_protein=extracted.get("total_protein"),
        total_cholesterol=extracted.get("total_cholesterol"),
        hdl=extracted.get("hdl"),
        ldl=extracted.get("ldl"),
        triglycerides=extracted.get("triglycerides"),
        vldl=extracted.get("vldl"),
        tsh=extracted.get("tsh"),
        t3=extracted.get("t3"),
        t4=extracted.get("t4"),
        vitamin_d=extracted.get("vitamin_d"),
        vitamin_b12=extracted.get("vitamin_b12"),
        iron=extracted.get("iron"),
        ferritin=extracted.get("ferritin"),
        calcium=extracted.get("calcium"),
        sodium=extracted.get("sodium"),
        potassium=extracted.get("potassium"),
        peripheral_smear=extracted.get("peripheral_smear"),
        lab_interpretation=extracted.get("lab_interpretation"),
        ocr_raw=json.dumps(extracted)
    )
    db.add(report)
    
    # 5. Update Status — create if missing
    result = await db.execute(select(UserDataStatus).where(UserDataStatus.user_id == user_id))
    status = result.scalar_one_or_none()
    if not status:
        status = UserDataStatus(user_id=user_id)
        db.add(status)

    # Only mark has_report=True if we actually extracted health values
    health_keys = ["hemoglobin", "rbc_count", "wbc_count", "platelet_count",
                   "fasting_glucose", "random_glucose", "creatinine", "urea",
                   "hba1c", "sgpt", "total_cholesterol", "tsh", "vitamin_d", "vitamin_b12"]
    extracted_health_count = sum(1 for k in health_keys if extracted.get(k) is not None)
    if extracted_health_count > 0:
        status.has_report = True
        status.report_count += 1
        print(f"✅ Report marked valid — {extracted_health_count} health values extracted")
    else:
        print(f"⚠️ OCR extracted 0 health values — report saved but not marked as valid data source")
    
    await db.flush()
    
    print(f"📋 Report flushed for user {user_id}, hemoglobin={extracted.get('hemoglobin')}, platelets={extracted.get('platelet_count')}")

    # 6. Commit FIRST so the report is visible to the analysis query
    await db.commit()

    # 7. Trigger Full ML Analysis in a fresh session
    try:
        async with async_session() as analysis_db:
            analysis = await run_full_analysis(user_id, analysis_db)
            await analysis_db.commit()
        print(f"✅ Analysis complete: health_index={analysis.get('health_index') if analysis else 'None'}, "
              f"tasks={len(analysis.get('tasks', [])) if analysis else 0}, "
              f"care_items={len(analysis.get('preventive_care', [])) if analysis else 0}, "
              f"diet={analysis.get('diet', {}).get('focus_type') if analysis else 'None'}")
    except Exception as e:
        print(f"❌ Analysis pipeline error: {e}")
        import traceback
        traceback.print_exc()
        analysis = None
    # 7. Auto-create water reminders (hourly from 8AM to 9PM)
    try:
        from models.reminder import Reminder
        from sqlalchemy import select as sel
        existing_water = await db.execute(
            sel(Reminder).where(Reminder.user_id == user_id, Reminder.reminder_type == "water")
        )
        if len(existing_water.scalars().all()) < 5:
            water_hours = ["08:00", "09:00", "10:00", "11:00", "12:00", "13:00",
                           "14:00", "15:00", "16:00", "17:00", "18:00", "19:00",
                           "20:00", "21:00"]
            for hour in water_hours:
                db.add(Reminder(
                    user_id=user_id,
                    title="💧 Drink Water",
                    message="Time to hydrate! Drink a glass of water.",
                    reminder_time=hour,
                    reminder_type="water",
                    is_recurring=True,
                    is_active=True,
                ))
            print(f"💧 Created {len(water_hours)} water reminders for user {user_id}")
    except Exception as e:
        print(f"⚠️ Water reminders creation error: {e}")
    
    return {
        "message": "Report analyzed successfully",
        "extracted_values": extracted,
        "ml_analysis": {
            "summary": "Report analyzed with all your health data.",
            "health_index": analysis.get("health_index", 0) if analysis else 0,
        },
        "preventive_care": analysis.get("preventive_care", []) if analysis else [],
        "positive_precautions": [
            step for item in (analysis.get("preventive_care", []) if analysis else [])
            for step in item.get("prevention_steps", [])
        ][:6],
        "tasks_generated": analysis.get("tasks", []) if analysis else [],
        "diet_plan": analysis.get("diet", {}) if analysis else {}
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
