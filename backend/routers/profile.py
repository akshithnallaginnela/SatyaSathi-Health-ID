from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import shutil, os, uuid, json
from pydantic import BaseModel

from database import get_db
from models.domain import User, CoinLedger, BloodReport, BPReading, SugarReading
from security.jwt_handler import get_current_user_id
from security.encryption import hash_password, verify_password

router = APIRouter(prefix="/api/profile", tags=["Profile"])

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads", "profiles")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/")
async def get_profile(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": str(user.id),
        "health_id": user.health_id,
        "full_name": user.full_name,
        "phone_number": user.phone_number,
        "gender": user.gender,
        "blood_group": user.blood_group,
        "date_of_birth": str(user.date_of_birth) if user.date_of_birth else None,
        "bmi": float(user.bmi) if user.bmi else None,
        "weight_kg": float(user.weight_kg) if user.weight_kg else None,
        "height_cm": float(user.height_cm) if user.height_cm else None,
        "waist_cm": float(user.waist_cm) if user.waist_cm else None,
        "profile_photo_url": user.profile_photo_url,
        "aadhaar_verified": bool(user.aadhaar_verified) if hasattr(user, 'aadhaar_verified') else False,
        "aadhaar_last4": getattr(user, 'aadhaar_last4', None),
        "created_at": str(user.created_at) if hasattr(user, 'created_at') and user.created_at else None,
    }


@router.put("/update")
async def update_profile(
    data: dict,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if "full_name" in data and data["full_name"]:
        user.full_name = data["full_name"]
    if "gender" in data:
        user.gender = data["gender"]
    if "date_of_birth" in data and data["date_of_birth"]:
        from datetime import date
        try:
            user.date_of_birth = date.fromisoformat(data["date_of_birth"])
        except Exception:
            pass
    # Update weight/height/BMI
    if "weight_kg" in data and data["weight_kg"]:
        user.weight_kg = float(data["weight_kg"])
    if "height_cm" in data and data["height_cm"]:
        user.height_cm = float(data["height_cm"])
    if user.weight_kg and user.height_cm:
        user.bmi = round(user.weight_kg / ((user.height_cm / 100) ** 2), 2)
    await db.commit()
    return {
        "id": str(user.id),
        "health_id": user.health_id,
        "full_name": user.full_name,
        "phone_number": user.phone_number,
        "gender": user.gender,
        "date_of_birth": str(user.date_of_birth) if user.date_of_birth else None,
        "bmi": float(user.bmi) if user.bmi else None,
        "weight_kg": float(user.weight_kg) if user.weight_kg else None,
        "height_cm": float(user.height_cm) if user.height_cm else None,
        "profile_photo_url": user.profile_photo_url,
        "aadhaar_verified": bool(user.aadhaar_verified) if hasattr(user, 'aadhaar_verified') else False,
        "aadhaar_last4": getattr(user, 'aadhaar_last4', None),
    }


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


@router.post("/change-password")
async def change_password(
    data: PasswordChange,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")
    user.password_hash = hash_password(data.new_password)
    await db.commit()
    return {"message": "Password changed successfully"}


@router.get("/download-report")
async def download_health_report(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Generate a full health summary JSON for the user to download."""
    user_res = await db.execute(select(User).where(User.id == user_id))
    user = user_res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    bp_res = await db.execute(
        select(BPReading).where(BPReading.user_id == user_id)
        .order_by(desc(BPReading.measured_at)).limit(30)
    )
    bp_list = bp_res.scalars().all()

    sugar_res = await db.execute(
        select(SugarReading).where(SugarReading.user_id == user_id)
        .order_by(desc(SugarReading.measured_at)).limit(30)
    )
    sugar_list = sugar_res.scalars().all()

    report_res = await db.execute(
        select(BloodReport).where(BloodReport.user_id == user_id)
        .order_by(desc(BloodReport.uploaded_at)).limit(5)
    )
    reports = report_res.scalars().all()

    summary = {
        "health_id": user.health_id,
        "full_name": user.full_name,
        "gender": user.gender,
        "date_of_birth": str(user.date_of_birth) if user.date_of_birth else None,
        "bmi": user.bmi,
        "weight_kg": user.weight_kg,
        "height_cm": user.height_cm,
        "bp_readings": [
            {"systolic": r.systolic, "diastolic": r.diastolic, "pulse": r.pulse, "date": str(r.date)}
            for r in bp_list
        ],
        "sugar_readings": [
            {"fasting_glucose": r.fasting_glucose, "date": str(r.date)}
            for r in sugar_list
        ],
        "blood_reports": [
            {
                "lab_name": r.lab_name,
                "report_date": str(r.report_date),
                "hemoglobin": r.hemoglobin,
                "platelet_count": r.platelet_count,
                "wbc_count": r.wbc_count,
                "fasting_glucose": r.fasting_glucose,
            }
            for r in reports
        ],
        "generated_at": str(__import__("datetime").datetime.utcnow()),
    }
    return JSONResponse(content=summary, headers={
        "Content-Disposition": f'attachment; filename="vitalid_report_{user.health_id}.json"'
    })


@router.get("/activity")
async def get_activity(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CoinLedger).where(CoinLedger.user_id == user_id)
        .order_by(desc(CoinLedger.created_at)).limit(20)
    )
    history = result.scalars().all()
    return {
        "completed_tasks": [
            {
                "id": str(h.id),
                "name": h.activity_type.replace("TASK_COMPLETION_", "").replace("_", " ").title(),
                "coins": h.amount,
                "date": str(h.created_at)
            } for h in history
        ]
    }


@router.post("/upload-photo")
async def upload_photo(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    file_ext = file.filename.split(".")[-1]
    file_name = f"{user_id}_{uuid.uuid4().hex}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, file_name)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    user.profile_photo_url = f"/uploads/profiles/{file_name}"
    await db.commit()
    return {"photo_url": user.profile_photo_url, "profile_photo_url": user.profile_photo_url}
