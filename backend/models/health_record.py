"""
Health record models — Vitals log + Body metrics.
"""

import uuid
from datetime import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Integer, DateTime, Numeric, ForeignKey
from database import Base


# ─── SQLAlchemy Models ───

class VitalsLog(Base):
    __tablename__ = "vitals_log"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    systolic = Column(Integer, nullable=True)
    diastolic = Column(Integer, nullable=True)
    pulse = Column(Integer, nullable=True)
    fasting_glucose = Column(Numeric(6, 2), nullable=True)
    spo2 = Column(Integer, nullable=True)
    body_temp = Column(Numeric(4, 1), nullable=True)
    measured_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    source = Column(String(20), default="manual")  # manual, device, ocr


class BodyMetrics(Base):
    __tablename__ = "body_metrics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    weight_kg = Column(Numeric(5, 2), nullable=True)
    height_cm = Column(Numeric(5, 1), nullable=True)
    bmi = Column(Numeric(4, 1), nullable=True)
    waist_cm = Column(Numeric(5, 1), nullable=True)
    measured_at = Column(DateTime, default=datetime.utcnow)


# ─── Pydantic Schemas ───

class BPReading(BaseModel):
    systolic: int = Field(..., ge=60, le=250)
    diastolic: int = Field(..., ge=30, le=150)
    pulse: Optional[int] = Field(None, ge=30, le=220)
    measured_at: Optional[datetime] = None


class GlucoseReading(BaseModel):
    fasting_glucose: float = Field(..., ge=30, le=600)
    measured_at: Optional[datetime] = None


class BMIEntry(BaseModel):
    weight_kg: float = Field(..., ge=20, le=300)
    height_cm: float = Field(..., ge=50, le=250)
    waist_cm: Optional[float] = Field(None, ge=30, le=200)


class VitalsResponse(BaseModel):
    id: str
    systolic: Optional[int] = None
    diastolic: Optional[int] = None
    pulse: Optional[int] = None
    fasting_glucose: Optional[float] = None
    spo2: Optional[int] = None
    measured_at: datetime
    source: str = "manual"

    class Config:
        from_attributes = True


class BodyMetricsResponse(BaseModel):
    id: str
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    bmi: Optional[float] = None
    waist_cm: Optional[float] = None
    measured_at: datetime

    class Config:
        from_attributes = True
