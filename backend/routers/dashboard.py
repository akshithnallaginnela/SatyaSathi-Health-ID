"""
Dashboard router — single summary endpoint for the home screen.
"""

from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from database import get_db
from models.user import User
from models.health_record import VitalsLog
from models.task import DailyTask
from models.coin_ledger import CoinLedger
from models.report import Report
from security.jwt_handler import get_current_user_id

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


def _calculate_wellness_score(
    latest_vitals: VitalsLog | None,
    tasks_done: int,
    tasks_total: int,
    streak: int,
    latest_report: Report | None,
) -> int:
    """Compute a practical MVP wellness score from vitals + adherence."""
    score = 55.0

    if latest_vitals:
        # Blood pressure contribution
        if latest_vitals.systolic and latest_vitals.diastolic:
            sys = latest_vitals.systolic
            dia = latest_vitals.diastolic
            if sys <= 120 and dia <= 80:
                score += 15
            elif sys <= 140 and dia <= 90:
                score += 8
            else:
                score -= 10

        # Glucose contribution
        if latest_vitals.fasting_glucose is not None:
            glucose = float(latest_vitals.fasting_glucose)
            if 70 <= glucose <= 99:
                score += 12
            elif glucose <= 125:
                score += 6
            else:
                score -= 10

        # Pulse contribution
        if latest_vitals.pulse is not None:
            pulse = latest_vitals.pulse
            if 60 <= pulse <= 100:
                score += 6
            else:
                score -= 4

    # Task adherence contribution
    if tasks_total > 0:
        completion_ratio = tasks_done / tasks_total
        score += completion_ratio * 18

    # Streak bonus, capped to avoid dominance
    score += min(streak, 14) * 0.8

    # Report risk adjustment from latest ML analysis (positive framing still shown in UI)
    if latest_report and isinstance(latest_report.extracted_values, dict):
        risk_level = ((latest_report.extracted_values or {}).get("ml_analysis") or {}).get("risk_level")
        if risk_level == "high":
            score -= 12
        elif risk_level == "moderate":
            score -= 6
        elif risk_level == "low":
            score += 3

    return int(max(0, min(100, round(score))))


@router.get("/summary")
async def get_dashboard_summary(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated dashboard data for the home screen."""

    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    # Get latest vitals
    result = await db.execute(
        select(VitalsLog)
        .where(VitalsLog.user_id == user_id)
        .order_by(desc(VitalsLog.measured_at))
        .limit(1)
    )
    latest_vitals = result.scalar_one_or_none()

    # Get today's tasks
    today = date.today()
    result = await db.execute(
        select(DailyTask)
        .where(DailyTask.user_id == user_id, DailyTask.task_date == today)
    )
    todays_tasks = result.scalars().all()

    # Get coin balance
    result = await db.execute(
        select(func.coalesce(func.sum(CoinLedger.amount), 0))
        .where(CoinLedger.user_id == user_id)
    )
    coin_balance = result.scalar() or 0

    # Get latest processed report for preventive analytics
    result = await db.execute(
        select(Report)
        .where(Report.user_id == user_id)
        .order_by(desc(Report.uploaded_at))
        .limit(1)
    )
    latest_report = result.scalar_one_or_none()

    # Calculate streak (consecutive days with at least 1 completed task)
    streak = 0
    check_date = today - timedelta(days=1)
    while True:
        result = await db.execute(
            select(func.count())
            .select_from(DailyTask)
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

    # Week completion (Mon=0 to Sun=6 for this week)
    week_start = today - timedelta(days=today.weekday())
    week_completion = []
    for i in range(7):
        day = week_start + timedelta(days=i)
        result = await db.execute(
            select(func.count())
            .select_from(DailyTask)
            .where(
                DailyTask.user_id == user_id,
                DailyTask.task_date == day,
                DailyTask.completed == True,
            )
        )
        count = result.scalar()
        week_completion.append(bool(count and count > 0))

    # Build response
    initials = "".join(word[0].upper() for word in (user.full_name or "U").split()[:2])

    tasks_done = sum(1 for t in todays_tasks if t.completed)
    tasks_total = len(todays_tasks)

    wellness_score = _calculate_wellness_score(
        latest_vitals=latest_vitals,
        tasks_done=tasks_done,
        tasks_total=tasks_total,
        streak=streak,
        latest_report=latest_report,
    )

    report_ml = {}
    report_precautions = []
    report_type = None
    if latest_report and isinstance(latest_report.extracted_values, dict):
        report_ml = (latest_report.extracted_values or {}).get("ml_analysis") or {}
        report_precautions = (latest_report.extracted_values or {}).get("positive_precautions") or []
        report_type = latest_report.report_type

    return {
        "user": {
            "name": user.full_name if user else "User",
            "initials": initials,
            "health_id": user.health_id if user else None,
        },
        "wellness_score": wellness_score,
        "streak_days": streak,
        "week_completion": week_completion,
        "coin_balance": int(coin_balance),
        "todays_tasks": [
            {
                "id": t.id,
                "type": t.task_type,
                "name": t.task_name,
                "coins": t.coins_reward,
                "completed": t.completed,
                "time_slot": t.time_slot,
            }
            for t in todays_tasks
        ],
        "tasks_summary": f"{tasks_done}/{tasks_total} Done",
        "preventive_analytics": {
            "risk_level": report_ml.get("risk_level", "low"),
            "summary": report_ml.get("summary", "Keep tracking your daily habits to stay on course."),
            "positive_precautions": report_precautions,
            "report_type": report_type,
        },
        "vitals_snapshot": {
            "bp": f"{latest_vitals.systolic}/{latest_vitals.diastolic}" if latest_vitals and latest_vitals.systolic else None,
            "glucose": float(latest_vitals.fasting_glucose) if latest_vitals and latest_vitals.fasting_glucose else None,
            "pulse": latest_vitals.pulse if latest_vitals else None,
            "spo2": latest_vitals.spo2 if latest_vitals else None,
        } if latest_vitals else {},
    }
