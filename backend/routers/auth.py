"""
Auth router — register, OTP verify, Aadhaar, login, refresh.
OTP uses in-memory store (mock) by default, plug in Redis/Twilio for production.
Aadhaar is stored as SHA-256 hash for uniqueness — raw number never persisted.
"""

import random
import uuid
import time
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.user import User, UserCreate, UserLogin, UserResponse, OTPVerify, AadhaarVerify, TokenResponse
from security.encryption import hash_password, verify_password, hash_aadhaar, get_aadhaar_last4, mask_phone
from security.jwt_handler import create_access_token, create_refresh_token, create_temp_token, verify_token, get_current_user_id
from security.audit_log import log_event

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# ─── In-memory OTP store (replace with Redis in production) ───
_otp_store: dict[str, dict] = {}  # { phone: { "otp": "123456", "expires": timestamp, "attempts": 0 } }

MAX_OTP_ATTEMPTS = 5
OTP_EXPIRY_SECONDS = 600  # 10 minutes


def _generate_health_id() -> str:
    """Generate a unique 14-digit health ID: XX-XXXX-XXXX-XXXX."""
    state_code = random.randint(10, 36)  # 2-digit state code
    rest = uuid.uuid4().int % 10**12     # 12 random digits
    digits = f"{state_code}{rest:012d}"
    return f"{digits[:2]}-{digits[2:6]}-{digits[6:10]}-{digits[10:14]}"


def _generate_otp() -> str:
    """Generate a 6-digit OTP."""
    return f"{random.randint(100000, 999999)}"


# ═══════════════════════════════════════
# POST /api/auth/register
# ═══════════════════════════════════════

@router.post("/register")
async def register(data: UserCreate, request: Request, db: AsyncSession = Depends(get_db)):
    """Register a new user. Sends OTP to phone for verification."""

    # 1. Check phone not already registered
    result = await db.execute(select(User).where(User.phone_number == data.phone_number))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered.",
        )

    # 2. Hash password
    pwd_hash = hash_password(data.password)

    # 3. Generate unique health ID
    health_id = _generate_health_id()

    # 4. Create user
    user = User(
        full_name=data.full_name,
        phone_number=data.phone_number,
        password_hash=pwd_hash,
        date_of_birth=data.date_of_birth,
        gender=data.gender,
        health_id=health_id,
        status="pending_verification",
    )
    db.add(user)
    await db.flush()  # get the user.id

    # 5. Generate and store OTP (in-memory mock)
    otp = _generate_otp()
    _otp_store[data.phone_number] = {
        "otp": otp,
        "expires": time.time() + OTP_EXPIRY_SECONDS,
        "attempts": 0,
    }

    # In production: send OTP via Twilio
    # For dev fallback: prints OTP to console
    from services.sms_service import send_otp_sms
    send_otp_sms(data.phone_number, otp)

    # 6. Audit log
    await log_event(db, action="REGISTER", user_id=user.id,
                    ip_address=request.client.host if request.client else None)

    return {
        "message": "OTP sent",
        "phone": mask_phone(data.phone_number),
        "health_id": health_id,
        # DEV ONLY — remove in production:
        "dev_otp": otp,
    }


# ═══════════════════════════════════════
# POST /api/auth/verify-otp
# ═══════════════════════════════════════

@router.post("/verify-otp")
async def verify_otp(data: OTPVerify, db: AsyncSession = Depends(get_db)):
    """Verify the 6-digit OTP sent during registration."""

    stored = _otp_store.get(data.phone_number)

    # Check OTP exists
    if not stored:
        raise HTTPException(status_code=400, detail="No OTP found. Request a new one.")

    # Check expiry
    if time.time() > stored["expires"]:
        del _otp_store[data.phone_number]
        raise HTTPException(status_code=400, detail="OTP expired. Request a new one.")

    # Check max attempts
    if stored["attempts"] >= MAX_OTP_ATTEMPTS:
        del _otp_store[data.phone_number]
        raise HTTPException(status_code=429, detail="Too many attempts. Request a new OTP.")

    # Verify OTP
    if data.otp != stored["otp"]:
        stored["attempts"] += 1
        raise HTTPException(
            status_code=400,
            detail=f"Invalid OTP. {MAX_OTP_ATTEMPTS - stored['attempts']} attempts remaining.",
        )

    # OTP valid — update user status
    result = await db.execute(select(User).where(User.phone_number == data.phone_number))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    user.status = "phone_verified"
    del _otp_store[data.phone_number]

    # Generate temp token for Aadhaar step
    temp_token = create_temp_token({"user_id": user.id, "phone": data.phone_number})

    return {
        "message": "Phone verified successfully!",
        "temp_token": temp_token,
        "next_step": "aadhaar_verify",
    }


# ═══════════════════════════════════════
# POST /api/auth/aadhaar-verify
# ═══════════════════════════════════════

@router.post("/aadhaar-verify")
async def aadhaar_verify(
    data: AadhaarVerify,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(verify_token),
):
    """
    Store Aadhaar for uniqueness (hashed).
    The raw Aadhaar number is NEVER stored — only a SHA-256 hash
    and the last 4 digits for display.
    """
    user_id = payload["user_id"]

    # 1. Hash the Aadhaar for uniqueness check
    aadhaar_hashed = hash_aadhaar(data.aadhaar_number)

    # 2. Check if this Aadhaar is already linked to another account
    result = await db.execute(select(User).where(User.aadhaar_hash == aadhaar_hashed))
    existing = result.scalar_one_or_none()
    if existing and existing.id != user_id:
        raise HTTPException(
            status_code=400,
            detail="This Aadhaar is already linked to another account.",
        )

    # 3. Update user with Aadhaar hash + last 4
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    user.aadhaar_hash = aadhaar_hashed
    user.aadhaar_last4 = get_aadhaar_last4(data.aadhaar_number)
    user.aadhaar_verified = True
    user.status = "active"

    # 4. Generate full tokens
    access_token = create_access_token({"user_id": user.id})
    refresh_token = create_refresh_token({"user_id": user.id})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


# ═══════════════════════════════════════
# POST /api/auth/login
# ═══════════════════════════════════════

@router.post("/login")
async def login(data: UserLogin, request: Request, db: AsyncSession = Depends(get_db)):
    """Login with phone number and password."""

    # 1. Find user
    result = await db.execute(select(User).where(User.phone_number == data.phone_number))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid phone number or password.")

    # 2. Check account locked
    if user.account_locked:
        raise HTTPException(
            status_code=403,
            detail="Account locked due to too many failed attempts. Contact support.",
        )

    # 3. Verify password
    if not verify_password(data.password, user.password_hash):
        user.login_attempts += 1
        if user.login_attempts >= 5:
            user.account_locked = True
        await log_event(db, action="FAILED_LOGIN", user_id=user.id,
                        ip_address=request.client.host if request.client else None, success=False)
        raise HTTPException(status_code=401, detail="Invalid phone number or password.")

    # 4. Success — reset attempts, generate tokens
    user.login_attempts = 0
    access_token = create_access_token({"user_id": user.id})
    refresh_token = create_refresh_token({"user_id": user.id})

    await log_event(db, action="LOGIN", user_id=user.id,
                    ip_address=request.client.host if request.client else None)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


# ═══════════════════════════════════════
# POST /api/auth/refresh
# ═══════════════════════════════════════

@router.post("/refresh")
async def refresh_token(payload: dict = Depends(verify_token), db: AsyncSession = Depends(get_db)):
    """Refresh access token using a valid refresh token."""

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=400, detail="Not a refresh token.")

    user_id = payload["user_id"]
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    new_access = create_access_token({"user_id": user.id})
    new_refresh = create_refresh_token({"user_id": user.id})

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        user=UserResponse.model_validate(user),
    )


# ═══════════════════════════════════════
# GET /api/auth/me  (get current user profile)
# ═══════════════════════════════════════

@router.get("/me", response_model=UserResponse)
async def get_me(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    """Get the currently authenticated user's profile."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return UserResponse.model_validate(user)
