"""
Daily task model — gamified health tasks with coin rewards.
"""

import uuid
from datetime import datetime, date
from typing import Optional, Dict, Any
from pydantic import BaseModel
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.dialects.sqlite import JSON
from database import Base


class DailyTask(Base):
    __tablename__ = "daily_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    task_type = Column(String(50), nullable=False)  # LOG_BP, MORNING_WALK, WATER_INTAKE, etc.
    task_name = Column(String(100), nullable=False)
    coins_reward = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    task_date = Column(Date, nullable=False, index=True)
    time_slot = Column(String(20), default="all_day")  # morning, afternoon, evening, all_day
    verification_data = Column(JSON, nullable=True)     # extra data like step count, value logged


# ─── Pydantic Schemas ───

class TaskResponse(BaseModel):
    id: str
    task_type: str
    task_name: str
    coins_reward: int
    completed: bool
    completed_at: Optional[datetime] = None
    task_date: date
    time_slot: str = "all_day"

    class Config:
        from_attributes = True


class TaskComplete(BaseModel):
    verification_data: Optional[Dict[str, Any]] = None  # e.g. {"systolic": 120, "diastolic": 80}


class StreakResponse(BaseModel):
    current_streak: int
    longest_streak: int
    week_completion: list[bool]
