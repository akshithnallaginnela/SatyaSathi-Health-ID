"""
Report model — lab report uploads with OCR-extracted values.
"""

import uuid
from datetime import datetime, date
from typing import Optional, Dict, Any
from pydantic import BaseModel
from sqlalchemy import Column, String, DateTime, Numeric, Date, ForeignKey, Text
from sqlalchemy.dialects.sqlite import JSON
from database import Base
from models.domain import GUID


class Report(Base):
    __tablename__ = "reports"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    report_type = Column(String(50), nullable=False)  # blood_sugar, lipid_profile, cbc
    file_key = Column(String(255), nullable=False)     # S3 file key or local path
    extracted_values = Column(JSON, nullable=True)      # OCR-extracted lab values
    upload_status = Column(String(20), default="uploaded")  # uploaded, processing, processed, failed
    ocr_confidence = Column(Numeric(4, 2), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    report_date = Column(Date, nullable=True)


# ─── Pydantic Schemas ───

class ReportUploadRequest(BaseModel):
    report_type: str  # blood_sugar, lipid_profile, cbc
    report_date: Optional[date] = None


class ReportResponse(BaseModel):
    id: str
    report_type: str
    extracted_values: Optional[Dict[str, Any]] = None
    upload_status: str
    ocr_confidence: Optional[float] = None
    uploaded_at: datetime
    report_date: Optional[date] = None

    class Config:
        from_attributes = True
