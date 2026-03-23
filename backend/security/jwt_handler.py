"""
JWT token creation and verification.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "vitalid-dev-secret-key-change-in-prod")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_EXPIRE_DAYS = int(os.getenv("JWT_ACCESS_EXPIRE_DAYS", "7"))
REFRESH_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "30"))

security = HTTPBearer()


def create_access_token(user_id: str, phone_last4: str, aadhaar_verified: bool, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token with full payload required by spec."""
    to_encode = {
        "user_id": str(user_id),
        "phone_last4": phone_last4,
        "aadhaar_verified": aadhaar_verified,
        "type": "access"
    }
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=ACCESS_EXPIRE_DAYS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: str, phone_last4: str, aadhaar_verified: bool) -> str:
    """Create a JWT refresh token with full payload."""
    to_encode = {
        "user_id": str(user_id),
        "phone_last4": phone_last4,
        "aadhaar_verified": aadhaar_verified,
        "type": "refresh"
    }
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_temp_token(data: dict, minutes: int = 15) -> str:
    """Create a short-lived temp token (e.g. for Aadhaar step)."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    to_encode.update({"exp": expire, "type": "temp"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """FastAPI dependency to verify JWT token and return payload."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user_id",
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


def get_current_user_id(payload: dict = Depends(verify_token)) -> str:
    """Extract user_id from token payload."""
    return payload["user_id"]
