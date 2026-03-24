"""
User settings model — notification and app preference storage.
"""

import uuid
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from database import Base
from models.domain import GUID


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    notifications_enabled = Column(Boolean, default=True)
    reminder_enabled = Column(Boolean, default=True)
    reminder_time = Column(String(5), default="08:00")
    language = Column(String(20), default="en")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserSettingsResponse(BaseModel):
    notifications_enabled: bool
    reminder_enabled: bool
    reminder_time: str
    language: str

    class Config:
        from_attributes = True


class UserSettingsUpdate(BaseModel):
    notifications_enabled: bool | None = None
    reminder_enabled: bool | None = None
    reminder_time: str | None = None
    language: str | None = None
