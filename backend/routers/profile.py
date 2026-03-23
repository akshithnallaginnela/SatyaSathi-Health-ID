from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import shutil
import os
import uuid

from database import get_db
from models.domain import User, CoinLedger
from security.jwt_handler import get_current_user_id

router = APIRouter(prefix="/api/profile", tags=["Profile"])
settings_router = APIRouter(prefix="/api/settings", tags=["Settings"])

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads", "profiles")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/")
async def get_profile(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/activity")
async def get_activity(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    # Return recent coin ledger entries as "activity"
    result = await db.execute(
        select(CoinLedger)
        .where(CoinLedger.user_id == user_id)
        .order_by(desc(CoinLedger.created_at))
        .limit(20)
    )
    history = result.scalars().all()
    # Frontend expects an object with completed_tasks key
    return {
        "completed_tasks": [
            {
                "id": str(h.id),
                "name": h.activity_type.replace("TASK_COMPLETION_", "").replace("_", " ").title(),
                "coins": h.amount,
                "date": h.created_at
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
    
    return {"photo_url": user.profile_photo_url}

@settings_router.get("/")
async def get_settings(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    # For prototype, return basic user flags
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    return {
        "notifications_enabled": True,
        "privacy_mode": False,
        "language": "en"
    }
