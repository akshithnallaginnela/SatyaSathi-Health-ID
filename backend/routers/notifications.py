from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from database import get_db
from models.domain import User
from security.jwt_handler import get_current_user_id

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

@router.get("/")
async def list_notifications(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Return mock notifications."""
    return [
        {
            "id": "n1",
            "title": "Welcome to VitalID!",
            "message": "Start by logging your morning BP.",
            "type": "info",
            "created_at": "2026-03-23T10:00:00Z",
            "read": False
        },
        {
            "id": "n2",
            "title": "Health Goal Achieved",
            "message": "You've logged 10,000 steps today!",
            "type": "success",
            "created_at": "2026-03-23T12:00:00Z",
            "read": True
        }
    ]

@router.post("/test")
async def create_test_notification():
    return {"message": "Test notification created"}
