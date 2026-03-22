"""
Notifications router — basic in-app notification feed for MVP.
"""

from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from security.jwt_handler import get_current_user_id
from security.audit_log import log_event

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

# Simple in-memory feed for MVP/demo. Replace with DB table + push provider in production.
_notification_store: dict[str, list[dict]] = {}


@router.get("/")
async def list_notifications(user_id: str = Depends(get_current_user_id)):
    """Get latest in-app notifications for current user."""
    return _notification_store.get(user_id, [])[-30:][::-1]


@router.post("/test")
async def create_test_notification(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a test notification to validate notification flow quickly."""
    payload = {
        "id": f"notif_{int(datetime.utcnow().timestamp())}",
        "title": "Health Reminder",
        "message": "Time to log your BP and complete one mission.",
        "created_at": datetime.utcnow().isoformat(),
        "read": False,
    }

    _notification_store.setdefault(user_id, []).append(payload)
    await log_event(db, action="NOTIFICATION_TEST", user_id=user_id, metadata=payload)

    return {"message": "Test notification created.", "notification": payload}
