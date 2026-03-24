"""
Notifications & Reminders router — handles custom reminders with notification text.
Also sets up automatic water reminders when reports are initialized.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from database import get_db
from models.reminder import Reminder
from models.domain import UserDataStatus
from security.jwt_handler import get_current_user_id

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


# ─── Pydantic Schemas ───

class ReminderCreate(BaseModel):
    title: str                    # e.g., "Take BP tablet"
    message: str                  # Custom notification message shown at reminder time
    reminder_time: str            # HH:MM format
    reminder_type: str = "custom" # custom, water, bp_check, sugar_check
    is_recurring: bool = False    # Daily recurring?


class ReminderUpdate(BaseModel):
    title: Optional[str] = None
    message: Optional[str] = None
    reminder_time: Optional[str] = None
    is_active: Optional[bool] = None
    is_recurring: Optional[bool] = None


class ReminderResponse(BaseModel):
    id: str
    title: str
    message: str
    reminder_time: str
    reminder_type: str
    is_recurring: bool
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


# ─── Get All Reminders ───

@router.get("/")
async def list_reminders(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get all reminders for the current user."""
    result = await db.execute(
        select(Reminder)
        .where(Reminder.user_id == user_id)
        .order_by(desc(Reminder.created_at))
    )
    reminders = result.scalars().all()
    
    return [
        {
            "id": str(r.id),
            "title": r.title,
            "message": r.message,
            "reminder_time": r.reminder_time,
            "reminder_type": r.reminder_type,
            "is_recurring": r.is_recurring,
            "is_active": r.is_active,
            "created_at": str(r.created_at) if r.created_at else None,
        }
        for r in reminders
    ]


# ─── Create a Custom Reminder ───

@router.post("/")
async def create_reminder(
    data: ReminderCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new custom reminder with notification text."""
    if not data.title or not data.message:
        raise HTTPException(status_code=400, detail="Title and message are required.")
    
    # Validate time format
    try:
        datetime.strptime(data.reminder_time, "%H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="Time must be in HH:MM format.")
    
    reminder = Reminder(
        user_id=user_id,
        title=data.title,
        message=data.message,
        reminder_time=data.reminder_time,
        reminder_type=data.reminder_type,
        is_recurring=data.is_recurring,
        is_active=True,
    )
    db.add(reminder)
    await db.commit()
    
    return {
        "id": str(reminder.id),
        "title": reminder.title,
        "message": reminder.message,
        "reminder_time": reminder.reminder_time,
        "reminder_type": reminder.reminder_type,
        "is_recurring": reminder.is_recurring,
        "is_active": reminder.is_active,
        "status": "created",
    }


# ─── Update a Reminder ───

@router.put("/{reminder_id}")
async def update_reminder(
    reminder_id: str,
    data: ReminderUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing reminder."""
    result = await db.execute(
        select(Reminder).where(Reminder.id == reminder_id, Reminder.user_id == user_id)
    )
    reminder = result.scalar_one_or_none()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found.")
    
    if data.title is not None:
        reminder.title = data.title
    if data.message is not None:
        reminder.message = data.message
    if data.reminder_time is not None:
        reminder.reminder_time = data.reminder_time
    if data.is_active is not None:
        reminder.is_active = data.is_active
    if data.is_recurring is not None:
        reminder.is_recurring = data.is_recurring
    
    await db.commit()
    return {"status": "updated", "id": str(reminder.id)}


# ─── Delete a Reminder ───

@router.delete("/{reminder_id}")
async def delete_reminder(
    reminder_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a reminder."""
    result = await db.execute(
        select(Reminder).where(Reminder.id == reminder_id, Reminder.user_id == user_id)
    )
    reminder = result.scalar_one_or_none()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found.")
    
    await db.delete(reminder)
    await db.commit()
    return {"status": "deleted"}


# ─── Initialize Water Reminders (called after report upload) ───

@router.post("/init-water-reminders")
async def init_water_reminders(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Create hourly water drinking reminders from 8 AM to 9 PM.
    Called after report initialization.
    """
    # Check if water reminders already exist
    result = await db.execute(
        select(Reminder).where(
            Reminder.user_id == user_id,
            Reminder.reminder_type == "water",
        )
    )
    existing = result.scalars().all()
    if len(existing) >= 5:
        return {"status": "already_initialized", "count": len(existing)}
    
    # Create hourly water reminders from 8 AM to 9 PM
    water_hours = ["08:00", "09:00", "10:00", "11:00", "12:00", "13:00", 
                   "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", 
                   "20:00", "21:00"]
    
    created = 0
    for hour in water_hours:
        reminder = Reminder(
            user_id=user_id,
            title="💧 Drink Water",
            message=f"Time to hydrate! Drink a glass of water. Staying hydrated supports your BP, kidney function, and overall health.",
            reminder_time=hour,
            reminder_type="water",
            is_recurring=True,
            is_active=True,
        )
        db.add(reminder)
        created += 1
    
    await db.commit()
    return {"status": "initialized", "count": created}


# ─── Get Active Reminders for Current Time ───

@router.get("/check")
async def check_due_reminders(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Check for reminders that are due right now."""
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    
    result = await db.execute(
        select(Reminder).where(
            Reminder.user_id == user_id,
            Reminder.is_active == True,
            Reminder.reminder_time == current_time,
        )
    )
    due_reminders = result.scalars().all()
    
    return [
        {
            "id": str(r.id),
            "title": r.title,
            "message": r.message,
            "reminder_type": r.reminder_type,
        }
        for r in due_reminders
    ]
