"""
Settings router — user app preferences.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from security.jwt_handler import get_current_user_id
from models.user_settings import UserSettings, UserSettingsResponse, UserSettingsUpdate

router = APIRouter(prefix="/api/settings", tags=["Settings"])


async def _get_or_create_settings(user_id: str, db: AsyncSession) -> UserSettings:
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == user_id))
    settings = result.scalar_one_or_none()
    if settings:
        return settings

    settings = UserSettings(user_id=user_id)
    db.add(settings)
    await db.flush()
    return settings


@router.get("/", response_model=UserSettingsResponse)
async def get_settings(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's app settings."""
    settings = await _get_or_create_settings(user_id, db)
    return UserSettingsResponse.model_validate(settings)


@router.put("/", response_model=UserSettingsResponse)
async def update_settings(
    data: UserSettingsUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's app settings."""
    settings = await _get_or_create_settings(user_id, db)

    if data.notifications_enabled is not None:
        settings.notifications_enabled = data.notifications_enabled
    if data.reminder_enabled is not None:
        settings.reminder_enabled = data.reminder_enabled
    if data.reminder_time is not None:
        settings.reminder_time = data.reminder_time
    if data.language is not None:
        settings.language = data.language

    await db.flush()
    return UserSettingsResponse.model_validate(settings)
