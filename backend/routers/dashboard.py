import json
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from database import get_db
from models.domain import (
    User, UserDataStatus, BPReading, SugarReading, 
    DailyTask, PreventiveCare, DietRecommendation, CoinLedger
)
from security.jwt_handler import get_current_user_id

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/summary")
async def get_dashboard_summary(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    # 1. Get User and Status
    user_res = await db.execute(select(User).where(User.id == user_id))
    user = user_res.scalar_one_or_none()
    
    status_res = await db.execute(select(UserDataStatus).where(UserDataStatus.user_id == user_id))
    status = status_res.scalar_one_or_none()

    # 2. Get Today's Tasks
    today = date.today()
    tasks_res = await db.execute(
        select(DailyTask).where(DailyTask.user_id == user_id, DailyTask.task_date == today)
    )
    tasks = tasks_res.scalars().all()

    # 3. Get Preventive Care
    care_res = await db.execute(
        select(PreventiveCare).where(PreventiveCare.user_id == user_id).order_by(desc(PreventiveCare.urgency))
    )
    care_items = care_res.scalars().all()

    # 4. Get Diet Plan
    diet_res = await db.execute(select(DietRecommendation).where(DietRecommendation.user_id == user_id))
    diet = diet_res.scalar_one_or_none()

    # 5. Get Latest Vitals
    bp_res = await db.execute(
        select(BPReading).where(BPReading.user_id == user_id).order_by(desc(BPReading.date)).limit(1)
    )
    latest_bp = bp_res.scalar_one_or_none()
    
    sugar_res = await db.execute(
        select(SugarReading).where(SugarReading.user_id == user_id).order_by(desc(SugarReading.date)).limit(1)
    )
    latest_sugar = sugar_res.scalar_one_or_none()

    # 6. Get Coin Balance
    coin_res = await db.execute(
        select(func.coalesce(func.sum(CoinLedger.amount), 0)).where(CoinLedger.user_id == user_id)
    )
    coin_balance = coin_res.scalar() or 0

    # 7. Helper for Task parsing
    formatted_tasks = []
    for t in tasks:
        formatted_tasks.append({
            "id": str(t.id),
            "name": t.task_name,
            "category": t.category,
            "completed": t.completed,
            "coins": t.coins_reward,
            "why": t.why_this_task
        })

    # 8. Helper for Preventive Care parsing
    formatted_care = []
    for c in care_items:
        formatted_care.append({
            "category": c.category,
            "urgency": c.urgency,
            "status": c.current_value,
            "risk": c.future_risk_message,
            "steps": json.loads(c.prevention_steps) if c.prevention_steps else [],
            "horizon": c.risk_horizon
        })

    # 9. Helper for Diet Plan
    formatted_diet = None
    if diet:
        formatted_diet = {
            "focus": diet.focus_type,
            "reason": diet.reason,
            "eat_more": json.loads(diet.eat_more) if diet.eat_more else [],
            "reduce": json.loads(diet.reduce) if diet.reduce else [],
            "avoid": json.loads(diet.avoid) if diet.avoid else [],
            "hydration": diet.hydration_goal_glasses
        }

    # 10. Health Index (Mock for now, but dynamic)
    health_index = 85
    if status and not status.has_report:
        health_index = 70 # Lower if no report
    
    return {
        "health_index": health_index,
        "health_id": user.health_id if user else None,
        "has_report": status.has_report if status else False,
        "coin_balance": coin_balance,
        "vitals": {
            "bp": f"{latest_bp.systolic}/{latest_bp.diastolic}" if latest_bp else "No data",
            "sugar": f"{latest_sugar.fasting_glucose} mg/dL" if latest_sugar else "No data"
        },
        "tasks": formatted_tasks,
        "preventive_care": formatted_care,
        "diet_plan": formatted_diet
    }
