import random
import uuid
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.domain import (
    User, UserDataStatus, UserCreate, UserLogin, UserResponse, 
    OTPVerify, AadhaarSubmit, TokenResponse
)
from security.encryption import hash_password, verify_password, mask_phone
from security.jwt_handler import (
    create_access_token, create_refresh_token, create_temp_token, 
    verify_token, get_current_user_id
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# In-memory OTP store (mock for prototype)
_otp_store: dict[str, str] = {} # { phone: otp }

def _generate_health_id() -> str:
    """Generate a unique 14-digit health ID: XX-XXXX-XXXX-XXXX."""
    digits = f"{random.randint(10, 99)}{random.randint(100000000000, 999999999999)}"
    return f"{digits[:2]}-{digits[2:6]}-{digits[6:10]}-{digits[10:14]}"

@router.post("/register")
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    # 1. Check phone not already registered
    result = await db.execute(select(User).where(User.phone_number == data.phone_number))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Phone number already registered.")

    # 2. Compute BMI if height/weight provided
    bmi = None
    if data.weight_kg and data.height_cm:
        bmi = round(data.weight_kg / ((data.height_cm / 100) ** 2), 2)

    # 3. Create user
    user = User(
        full_name=data.full_name,
        phone_number=data.phone_number,
        password_hash=hash_password(data.password),
        health_id=_generate_health_id(),
        date_of_birth=data.date_of_birth,
        gender=data.gender,
        weight_kg=data.weight_kg,
        height_cm=data.height_cm,
        bmi=bmi,
        waist_cm=data.waist_cm,
        smoking=data.smoking,
        alcohol=data.alcohol,
        activity_level=data.activity_level,
        stress_level=data.stress_level,
        family_hx_diabetes=data.family_hx_diabetes,
        family_hx_heart=data.family_hx_heart,
        medications=json.dumps(data.medications)
    )
    db.add(user)
    await db.flush()

    # 4. Initialize Data Status
    status_entry = UserDataStatus(user_id=user.id)
    db.add(status_entry)
    
    await db.commit()

    # 5. Save and send OTP (Mock)
    otp = "123456" # Fixed mock OTP
    _otp_store[data.phone_number] = otp

    return {
        "message": "User registered. OTP sent.",
        "phone": mask_phone(data.phone_number),
        "dev_otp": otp # For prototype testing
    }

@router.post("/verify-otp")
async def verify_otp(data: OTPVerify, db: AsyncSession = Depends(get_db)):
    stored_otp = _otp_store.get(data.phone_number)
    if not stored_otp or data.otp != stored_otp:
        raise HTTPException(status_code=400, detail="Invalid OTP.")

    result = await db.execute(select(User).where(User.phone_number == data.phone_number))
    user = result.scalar_one_or_none()
    
    # Clean up OTP
    if data.phone_number in _otp_store:
        del _otp_store[data.phone_number]

    # Generate temp token for Aadhaar submit step
    temp_token = create_temp_token({"user_id": str(user.id)})
    
    return {
        "message": "Phone verified.",
        "temp_token": temp_token,
        "next_step": "aadhaar_submit"
    }

@router.post("/aadhaar-submit")
async def aadhaar_submit(data: AadhaarSubmit, db: AsyncSession = Depends(get_db), payload: dict = Depends(verify_token)):
    user_id = payload["user_id"]
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    user.aadhaar_last4 = data.aadhaar_number[-4:]
    user.aadhaar_verified = True
    
    await db.commit()
    
    # Return full tokens after Aadhaar
    access_token = create_access_token(user.id, user.phone_number[-4:], user.aadhaar_verified)
    refresh_token = create_refresh_token(user.id, user.phone_number[-4:], user.aadhaar_verified)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user)
    )

@router.post("/login")
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.phone_number == data.phone_number))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid phone or password.")

    access_token = create_access_token(user.id, user.phone_number[-4:], user.aadhaar_verified)
    refresh_token = create_refresh_token(user.id, user.phone_number[-4:], user.aadhaar_verified)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user)
    )

@router.get("/me", response_model=UserResponse)
async def get_me(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return UserResponse.model_validate(user)
