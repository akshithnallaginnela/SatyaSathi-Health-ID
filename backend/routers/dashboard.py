import json
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from database import get_db
from models.domain import (
    User, UserDataStatus, BPReading, SugarReading, BloodReport,
    DailyTask, PreventiveCare, DietRecommendation, CoinLedger
)
from security.jwt_handler import get_current_user_id
from ml.analysis_engine import (
    get_user, get_bp_readings, get_sugar_readings, get_latest_report,
    build_features, calculate_health_index
)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/summary")
async def get_dashboard_summary(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    # 1. Get User and Status
    user = await get_user(user_id, db)
    
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
        select(PreventiveCare).where(PreventiveCare.user_id == user_id)
        .order_by(desc(PreventiveCare.generated_at))
    )
    care_items = care_res.scalars().all()

    # 4. Get Diet Plan
    diet_res = await db.execute(select(DietRecommendation).where(DietRecommendation.user_id == user_id))
    diet = diet_res.scalar_one_or_none()

    # 5. Get Latest Vitals
    bp_readings = await get_bp_readings(user_id, db, limit=7)
    sugar_readings = await get_sugar_readings(user_id, db, limit=4)
    latest_report = await get_latest_report(user_id, db)
    
    latest_bp = bp_readings[0] if bp_readings else None
    latest_sugar = sugar_readings[0] if sugar_readings else None

    # 6. Get Coin Balance
    coin_res = await db.execute(
        select(func.coalesce(func.sum(CoinLedger.amount), 0)).where(CoinLedger.user_id == user_id)
    )
    coin_balance = coin_res.scalar() or 0

    # 7. REAL Health Index from ALL data
    features = build_features(user, bp_readings, sugar_readings, latest_report)
    health_index = calculate_health_index(features)

    # 8. Format Tasks
    formatted_tasks = []
    for t in tasks:
        formatted_tasks.append({
            "id": str(t.id),
            "name": t.task_name,
            "task_name": t.task_name,
            "category": t.category,
            "completed": t.completed,
            "coins": t.coins_reward,
            "coins_reward": t.coins_reward,
            "why": t.why_this_task
        })

    # 9. Format Preventive Care — include ALL items, not just first
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

    # 10. Format Diet Plan
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

    # 11. Determine what data we have
    has_data = False
    data_sources = []
    if status:
        if status.has_bp:
            has_data = True
            data_sources.append("BP")
        if status.has_sugar:
            has_data = True
            data_sources.append("Sugar")
        if status.has_report:
            has_data = True
            data_sources.append("Report")
    
    # Also mark as has_data if user has BMI
    if user and user.bmi:
        has_data = True
        data_sources.append("BMI")

    # 12. Determine highest urgency
    urgency_order = {"act_now": 3, "watch": 2, "maintain": 1, "info": 0}
    highest_urgency = "low"
    if formatted_care:
        max_care = max(formatted_care, key=lambda c: urgency_order.get(c["urgency"], 0))
        highest_urgency = max_care["urgency"]
    
    # 13. Build comprehensive preventive summary
    preventive_summary = "Keep tracking your daily habits."
    all_steps = []
    if formatted_care:
        summaries = [c["risk"] for c in formatted_care if c.get("risk")]
        if summaries:
            preventive_summary = summaries[0]
        for c in formatted_care:
            all_steps.extend(c.get("steps", []))
    
    # Deduplicate steps
    unique_steps = list(dict.fromkeys(all_steps))

    initials = "".join(word[0].upper() for word in (user.full_name or "U").split()[:2]) if user else "U"

    # Health index subtitle
    if health_index >= 80:
        health_subtitle = "Your vitals look great! Keep going."
    elif health_index >= 60:
        health_subtitle = "Mostly stable. A few areas need attention."
    elif health_index >= 40:
        health_subtitle = "Multiple vitals need attention."
    elif health_index > 0:
        health_subtitle = "Your health needs immediate focus."
    else:
        health_subtitle = "Log vitals to see your health index."

    return {
        "user": {
            "name": user.full_name if user else "User",
            "initials": initials,
            "health_id": user.health_id if user else None,
        },
        "health_index": health_index,
        "wellness_score": health_index,
        "health_subtitle": health_subtitle,
        "has_report": status.has_report if status else False,
        "has_data": has_data,
        "data_sources": data_sources,
        "coin_balance": int(coin_balance),
        "vitals_snapshot": {
            "bp": f"{latest_bp.systolic}/{latest_bp.diastolic}" if latest_bp else None,
            "glucose": float(latest_sugar.fasting_glucose) if latest_sugar else None,
            "bmi": float(user.bmi) if user and user.bmi else None,
            "weight": float(user.weight_kg) if user and user.weight_kg else None,
        },
        "todays_tasks": formatted_tasks,
        "preventive_analytics": {
            "risk_level": highest_urgency,
            "summary": preventive_summary,
            "positive_precautions": unique_steps[:8],  # Top 8 action items
            "all_care_items": formatted_care,
            "data_sources_used": data_sources,
            "report_type": "Blood Test" if status and status.has_report else None,
            "diet_plan": formatted_diet
        },
        "streak_days": 3  # Will be calculated from login events later
    }
