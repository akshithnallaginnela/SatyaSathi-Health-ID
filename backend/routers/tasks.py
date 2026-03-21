"""
Tasks router — daily task generation, completion, streaks, and history.
"""

import uuid
from datetime import date, datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_

from database import get_db
from models.task import DailyTask, TaskResponse, TaskComplete, StreakResponse
from models.coin_ledger import CoinLedger
from security.jwt_handler import get_current_user_id

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])

# Max coins a user can earn per day
MAX_DAILY_COINS = 50

# Default task templates
DEFAULT_TASKS = [
    {"type": "LOG_BP", "name": "Log Morning BP", "coins": 15, "time_slot": "morning"},
    {"type": "MORNING_WALK", "name": "20 Min Morning Walk", "coins": 25, "time_slot": "morning"},
    {"type": "LOG_BP", "name": "Log Afternoon BP", "coins": 15, "time_slot": "afternoon"},
    {"type": "DEEP_BREATHING", "name": "5 Min Deep Breathing", "coins": 10, "time_slot": "evening"},
    {"type": "WATER_INTAKE", "name": "Drink 8 Glasses Water", "coins": 8, "time_slot": "all_day"},
    {"type": "DIET_MEAL", "name": "Log Healthy Meal", "coins": 8, "time_slot": "afternoon"},
]


async def _ensure_today_tasks(user_id: str, db: AsyncSession):
    """Generate today's tasks if they don't exist yet."""
    today = date.today()
    result = await db.execute(
        select(func.count()).select_from(DailyTask)
        .where(DailyTask.user_id == user_id, DailyTask.task_date == today)
    )
    count = result.scalar()
    if count and count > 0:
        return  # Already generated

    for task_tmpl in DEFAULT_TASKS:
        task = DailyTask(
            user_id=user_id,
            task_type=task_tmpl["type"],
            task_name=task_tmpl["name"],
            coins_reward=task_tmpl["coins"],
            task_date=today,
            time_slot=task_tmpl["time_slot"],
        )
        db.add(task)
    await db.flush()


async def _get_daily_earned(user_id: str, db: AsyncSession) -> int:
    """Get total coins earned today."""
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    result = await db.execute(
        select(func.coalesce(func.sum(CoinLedger.amount), 0))
        .where(
            CoinLedger.user_id == user_id,
            CoinLedger.created_at >= today_start,
            CoinLedger.amount > 0,
        )
    )
    return result.scalar() or 0


@router.get("/today", response_model=list[TaskResponse])
async def get_today_tasks(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get today's task list (auto-generates if first call of the day)."""
    await _ensure_today_tasks(user_id, db)
    result = await db.execute(
        select(DailyTask)
        .where(DailyTask.user_id == user_id, DailyTask.task_date == date.today())
        .order_by(DailyTask.time_slot)
    )
    tasks = result.scalars().all()
    return [TaskResponse.model_validate(t) for t in tasks]


@router.post("/{task_id}/complete")
async def complete_task(
    task_id: str,
    data: TaskComplete = TaskComplete(),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Mark a task as completed and award coins."""
    result = await db.execute(
        select(DailyTask).where(DailyTask.id == task_id, DailyTask.user_id == user_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    if task.completed:
        raise HTTPException(status_code=400, detail="Task already completed.")

    # Anti-fraud: daily coin cap
    earned_today = await _get_daily_earned(user_id, db)
    coins_to_award = min(task.coins_reward, MAX_DAILY_COINS - earned_today)
    if coins_to_award <= 0:
        coins_to_award = 0

    # Mark task done
    task.completed = True
    task.completed_at = datetime.utcnow()
    task.verification_data = data.verification_data

    # Award coins
    if coins_to_award > 0:
        coin_entry = CoinLedger(
            user_id=user_id,
            amount=coins_to_award,
            activity_type=task.task_type,
        )
        db.add(coin_entry)

    await db.flush()

    return {
        "message": "Task completed!",
        "task_id": task_id,
        "coins_earned": coins_to_award,
        "daily_total": earned_today + coins_to_award,
        "daily_limit": MAX_DAILY_COINS,
    }


@router.get("/streak", response_model=StreakResponse)
async def get_streak(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get current streak and weekly completion."""
    today = date.today()
    streak = 0
    check_date = today - timedelta(days=1)

    while True:
        result = await db.execute(
            select(func.count()).select_from(DailyTask)
            .where(
                DailyTask.user_id == user_id,
                DailyTask.task_date == check_date,
                DailyTask.completed == True,
            )
        )
        count = result.scalar()
        if count and count > 0:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    # Check if today has completions too
    result = await db.execute(
        select(func.count()).select_from(DailyTask)
        .where(
            DailyTask.user_id == user_id,
            DailyTask.task_date == today,
            DailyTask.completed == True,
        )
    )
    today_count = result.scalar()
    if today_count and today_count > 0:
        streak += 1

    # Week completion
    week_start = today - timedelta(days=today.weekday())
    week_completion = []
    for i in range(7):
        day = week_start + timedelta(days=i)
        result = await db.execute(
            select(func.count()).select_from(DailyTask)
            .where(
                DailyTask.user_id == user_id,
                DailyTask.task_date == day,
                DailyTask.completed == True,
            )
        )
        count = result.scalar()
        week_completion.append(bool(count and count > 0))

    return StreakResponse(
        current_streak=streak,
        longest_streak=streak,  # simplified
        week_completion=week_completion,
    )


@router.get("/history")
async def get_task_history(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated task completion history."""
    offset = (page - 1) * limit
    result = await db.execute(
        select(DailyTask)
        .where(DailyTask.user_id == user_id, DailyTask.completed == True)
        .order_by(desc(DailyTask.completed_at))
        .offset(offset)
        .limit(limit)
    )
    tasks = result.scalars().all()
    return [TaskResponse.model_validate(t) for t in tasks]
