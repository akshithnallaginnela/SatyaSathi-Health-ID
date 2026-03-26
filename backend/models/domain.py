import uuid
from datetime import date, datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, Date, DateTime, Float, 
    Text, ForeignKey, ARRAY, text
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# SQLite fallback for UUID
class GUID(TypeDecorator):
    """Platform-independent GUID type."""
    impl = CHAR
    cache_ok = True
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID())
        else:
            return dialect.type_descriptor(CHAR(32))
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                return "%.32x" % value.int
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value

class User(Base):
    __tablename__ = "users"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(100), nullable=False)
    phone_number = Column(String(15), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    health_id = Column(String(20), unique=True, nullable=False)
    date_of_birth = Column(Date)
    gender = Column(String(10))
    blood_group = Column(String(5))
    weight_kg = Column(Float)
    height_cm = Column(Float)
    bmi = Column(Float)
    waist_cm = Column(Float)
    smoking = Column(Boolean, default=False)
    alcohol = Column(Boolean, default=False)
    activity_level = Column(Integer, default=1)
    stress_level = Column(Integer, default=5)
    family_hx_diabetes = Column(Boolean, default=False)
    family_hx_heart = Column(Boolean, default=False)
    medications = Column(Text, default="[]") 
    aadhaar_last4 = Column(String(4))
    aadhaar_verified = Column(Boolean, default=False)
    profile_photo_url = Column(String(255))
    step_goal = Column(Integer, default=6000)
    emergency_contact = Column(String(15))
    created_at = Column(DateTime, default=datetime.utcnow)

class UserDataStatus(Base):
    __tablename__ = "user_data_status"
    user_id = Column(GUID(), ForeignKey("users.id"), primary_key=True)
    has_bp = Column(Boolean, default=False)
    has_sugar = Column(Boolean, default=False)
    has_report = Column(Boolean, default=False)
    bp_count = Column(Integer, default=0)
    sugar_count = Column(Integer, default=0)
    report_count = Column(Integer, default=0)
    last_analysis_at = Column(DateTime)
    analysis_ready = Column(Boolean, default=False)

class BPReading(Base):
    __tablename__ = "bp_readings"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"))
    systolic = Column(Integer, nullable=False)
    diastolic = Column(Integer, nullable=False)
    pulse = Column(Integer)
    time_of_day = Column(String(20), default="morning")
    measured_at = Column(DateTime, default=datetime.utcnow)
    date = Column(Date, default=date.today)

class SugarReading(Base):
    __tablename__ = "sugar_readings"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"))
    fasting_glucose = Column(Float, nullable=False)
    measured_at = Column(DateTime, default=datetime.utcnow)
    date = Column(Date, default=date.today)

class BloodReport(Base):
    __tablename__ = "blood_reports"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"))
    file_path = Column(String(255))
    lab_name = Column(String(100))
    report_date = Column(Date)
    
    # CBC — RBC
    hemoglobin = Column(Float)
    rbc_count = Column(Float)
    pcv = Column(Float)
    mcv = Column(Float)
    mch = Column(Float)
    mchc = Column(Float)
    rdw = Column(Float)
    rdw_sd = Column(Float)
    mpv = Column(Float)

    # CBC — WBC
    wbc_count = Column(Float)
    neutrophils_pct = Column(Float)
    lymphocytes_pct = Column(Float)
    monocytes_pct = Column(Float)
    eosinophils_pct = Column(Float)
    basophils_pct = Column(Float)
    neutrophils_abs = Column(Float)
    lymphocytes_abs = Column(Float)
    monocytes_abs = Column(Float)
    eosinophils_abs = Column(Float)

    # Platelets
    platelet_count = Column(Float)
    p_lcr = Column(Float)

    # Sugar
    fasting_glucose = Column(Float)
    random_glucose = Column(Float)
    hba1c = Column(Float)

    # Kidney
    urea = Column(Float)
    creatinine = Column(Float)
    uric_acid = Column(Float)
    egfr = Column(Float)

    # Liver
    sgpt = Column(Float)
    sgot = Column(Float)
    bilirubin_total = Column(Float)
    bilirubin_direct = Column(Float)
    alkaline_phosphatase = Column(Float)
    albumin = Column(Float)
    total_protein = Column(Float)

    # Lipids
    total_cholesterol = Column(Float)
    hdl = Column(Float)
    ldl = Column(Float)
    triglycerides = Column(Float)
    vldl = Column(Float)

    # Thyroid
    tsh = Column(Float)
    t3 = Column(Float)
    t4 = Column(Float)

    # Vitamins & Minerals
    vitamin_d = Column(Float)
    vitamin_b12 = Column(Float)
    iron = Column(Float)
    ferritin = Column(Float)
    calcium = Column(Float)
    sodium = Column(Float)
    potassium = Column(Float)

    # Peripheral smear
    peripheral_smear = Column(Text)

    lab_interpretation = Column(Text)
    ocr_raw = Column(Text)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

class HealthSignal(Base):
    __tablename__ = "health_signals"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"))
    signal_type = Column(String(50))
    metric = Column(String(50))
    current_status = Column(String(20))
    trend_direction = Column(String(20))
    message = Column(Text)
    preventive_message = Column(Text)
    action_text = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)

class PreventiveCare(Base):
    __tablename__ = "preventive_care"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"))
    category = Column(String(50))
    risk_horizon = Column(String(255))
    current_value = Column(Text)
    trend_summary = Column(Text)
    future_risk_message = Column(Text)
    prevention_steps = Column(Text) 
    urgency = Column(String(20))
    generated_at = Column(DateTime, default=datetime.utcnow)

class DailyTask(Base):
    __tablename__ = "daily_tasks"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"))
    task_type = Column(String(50))
    task_name = Column(String(100))
    description = Column(Text)
    why_this_task = Column(Text)
    category = Column(String(30))
    time_of_day = Column(String(20))
    duration_or_quantity = Column(String(50))
    coins_reward = Column(Integer, default=10)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    task_date = Column(Date, default=date.today)

class DietRecommendation(Base):
    __tablename__ = "diet_recommendations"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"))
    focus_type = Column(String(200))
    eat_more = Column(Text) 
    reduce = Column(Text)
    avoid = Column(Text)
    hydration_goal_glasses = Column(Integer, default=8)
    reason = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)

class CoinLedger(Base):
    __tablename__ = "coin_ledger"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"))
    amount = Column(Integer, nullable=False)
    activity_type = Column(String(50))
    tx_hash = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"))
    action = Column(String(50))
    detail = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class BlockchainRecord(Base):
    __tablename__ = "blockchain_records"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    record_type = Column(String(30), nullable=False)   # "BP", "SUGAR", "BMI", "REPORT"
    record_date = Column(Date, nullable=False)
    data_hash = Column(String(64), nullable=False)     # SHA-256 of the payload
    tx_hash = Column(String(120), nullable=False)      # Polygon tx hash (or mock)
    summary = Column(String(200))                      # Human-readable e.g. "BP: 120/80"
    created_at = Column(DateTime, default=datetime.utcnow)
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
import re

# ─── Pydantic Schemas ───

class UserCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    phone_number: str = Field(..., min_length=10, max_length=15)
    password: str = Field(..., min_length=8)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    emergency_contact: Optional[str] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    waist_cm: Optional[float] = None
    smoking: bool = False
    alcohol: bool = False
    activity_level: int = 1
    stress_level: int = 5
    family_hx_diabetes: bool = False
    family_hx_heart: bool = False
    medications: Optional[List[str]] = []

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v):
        if not re.match(r"^\+?\d{10,15}$", v):
            raise ValueError("Invalid phone number format.")
        return v

class UserLogin(BaseModel):
    phone_number: str
    password: str

class AadhaarSubmit(BaseModel):
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

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    full_name: str
    phone_number: str
    health_id: str
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    emergency_contact: Optional[str] = None
    date_of_birth: Optional[date] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    bmi: Optional[float] = None
    aadhaar_verified: bool = False
    aadhaar_last4: Optional[str] = None
    profile_photo_url: Optional[str] = None
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

class BPCreate(BaseModel):
    systolic: int
    diastolic: int
    pulse: Optional[int] = None
    time_of_day: str = "morning"

class SugarCreate(BaseModel):
    fasting_glucose: float
