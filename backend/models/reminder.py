"""
Reminder model — user-created custom reminders with text messages.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from models.domain import Base, GUID

class Reminder(Base):
    __tablename__ = "reminders"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(100), nullable=False)         # e.g., "Take BP tablets"
    message = Column(Text, nullable=False)               # Custom notification text
    reminder_time = Column(String(5), nullable=False)     # HH:MM format
    reminder_type = Column(String(30), default="custom")  # custom, water, bp_check, sugar_check
    is_recurring = Column(Boolean, default=False)         # Daily recurring?
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_triggered = Column(DateTime, nullable=True)
