"""
User model — SQLAlchemy table + Pydantic schemas.
"""

import uuid
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Column, String, Boolean, Integer, Date, DateTime, Text
from sqlalchemy.dialects.sqlite import JSON
from database import Base
import re


# ─── SQLAlchemy Model ───

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name = Column(String(100), nullable=False)
    phone_number = Column(String(15), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(10), nullable=True)
    health_id = Column(String(20), unique=True, nullable=False, index=True)
    
    # Aadhaar — stored as hash for uniqueness, never raw
    aadhaar_hash = Column(String(255), unique=True, nullable=True, index=True)
    aadhaar_last4 = Column(String(4), nullable=True)
    aadhaar_verified = Column(Boolean, default=False)
    
    # Blockchain wallet
    wallet_address = Column(String(42), nullable=True)
    wallet_key_encrypted = Column(Text, nullable=True)
    
    # Account status
    status = Column(String(30), default="pending_verification")  # pending_verification, phone_verified, active
    login_attempts = Column(Integer, default=0)
    account_locked = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)


# ─── Pydantic Schemas ───

class UserCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    phone_number: str = Field(..., min_length=10, max_length=10)
    password: str = Field(..., min_length=8)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v):
        if not re.match(r"^[6-9]\d{9}$", v):
            raise ValueError("Invalid Indian phone number. Must be 10 digits starting with 6-9.")
        return v

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v):
        if v and v.lower() not in ["male", "female", "other"]:
            raise ValueError("Gender must be male, female, or other.")
        return v.lower() if v else v


class UserLogin(BaseModel):
    phone_number: str
    password: str


class AadhaarVerify(BaseModel):
    aadhaar_number: str = Field(..., min_length=12, max_length=12)

    @field_validator("aadhaar_number")
    @classmethod
    def validate_aadhaar(cls, v):
        if not re.match(r"^\d{12}$", v):
            raise ValueError("Aadhaar must be exactly 12 digits.")
        return v


class OTPVerify(BaseModel):
    phone_number: str
    otp: str = Field(..., min_length=6, max_length=6)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: str
    full_name: str
    phone_number: str
    health_id: str
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    aadhaar_verified: bool = False
    aadhaar_last4: Optional[str] = None
    wallet_address: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
