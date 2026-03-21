"""
Profile router — user profile management and activity log.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

from database import get_db
from models.user import User, UserResponse
from models.coin_ledger import CoinLedger
from models.task import DailyTask
from security.jwt_handler import get_current_user_id
from security.encryption import hash_password, verify_password

router = APIRouter(prefix="/api/profile", tags=["Profile"])


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)


@router.get("/", response_model=UserResponse)
async def get_profile(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get full user profile."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return UserResponse.model_validate(user)


@router.put("/update", response_model=UserResponse)
async def update_profile(
    data: ProfileUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update user profile fields."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if data.full_name is not None:
        user.full_name = data.full_name
    if data.gender is not None:
        user.gender = data.gender.lower()
    if data.date_of_birth is not None:
        user.date_of_birth = data.date_of_birth

    await db.flush()
    return UserResponse.model_validate(user)


@router.post("/change-password")
async def change_password(
    data: PasswordChange,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Change user password (requires old password)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")

    user.password_hash = hash_password(data.new_password)
    await db.flush()
    return {"message": "Password changed successfully."}


@router.get("/activity")
async def get_activity_log(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get recent activity (tasks + coin transactions)."""
    # Get recent coin transactions
    result = await db.execute(
        select(CoinLedger)
        .where(CoinLedger.user_id == user_id)
        .order_by(desc(CoinLedger.created_at))
        .limit(30)
    )
    coins = result.scalars().all()

    # Get recent completed tasks
    result = await db.execute(
        select(DailyTask)
        .where(DailyTask.user_id == user_id, DailyTask.completed == True)
        .order_by(desc(DailyTask.completed_at))
        .limit(30)
    )
    tasks = result.scalars().all()

    return {
        "coin_transactions": [
            {
                "id": c.id,
                "amount": c.amount,
                "type": c.activity_type,
                "tx_hash": c.tx_hash,
                "date": c.created_at.isoformat() if c.created_at else None,
            }
            for c in coins
        ],
        "completed_tasks": [
            {
                "id": t.id,
                "name": t.task_name,
                "type": t.task_type,
                "coins": t.coins_reward,
                "date": t.completed_at.isoformat() if t.completed_at else None,
            }
            for t in tasks
        ],
    }
