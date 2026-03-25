"""
Share Health Report API — Generate shareable health summary
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from database import get_db
from models.domain import User, BPReading, SugarReading, PreventiveCare
from security.jwt_handler import get_current_user_id

router = APIRouter(prefix="/api/share", tags=["Share"])


@router.get("/health-summary")
async def get_shareable_summary(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Generate shareable health summary for WhatsApp/SMS"""
    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return {"error": "User not found"}
    
    # Get latest BP
    bp_result = await db.execute(
        select(BPReading).where(BPReading.user_id == user_id)
        .order_by(desc(BPReading.measured_at)).limit(1)
    )
    latest_bp = bp_result.scalar_one_or_none()
    
    # Get latest Sugar
    sugar_result = await db.execute(
        select(SugarReading).where(SugarReading.user_id == user_id)
        .order_by(desc(SugarReading.measured_at)).limit(1)
    )
    latest_sugar = sugar_result.scalar_one_or_none()
    
    # Get top 3 preventive care items
    care_result = await db.execute(
        select(PreventiveCare).where(PreventiveCare.user_id == user_id)
        .order_by(desc(PreventiveCare.generated_at)).limit(3)
    )
    care_items = care_result.scalars().all()
    
    # Get health score from user data status
    from models.domain import UserDataStatus
    status_result = await db.execute(
        select(UserDataStatus).where(UserDataStatus.user_id == user_id)
    )
    status = status_result.scalar_one_or_none()
    
    # Build shareable text
    lines = [
        f"🏥 *{user.full_name}'s Health Report*",
        f"VitalID: {user.health_id}",
        ""
    ]
    
    # Add health score if available
    if status and hasattr(status, 'health_index'):
        score = getattr(status, 'health_index', 0)
        if score >= 75:
            emoji = "🟢"
            label = "Good"
        elif score >= 50:
            emoji = "🟡"
            label = "Moderate"
        else:
            emoji = "🔴"
            label = "Needs Attention"
        lines.append(f"{emoji} Health Score: {score}/100 ({label})")
        lines.append("")
    
    # Add vitals
    if latest_bp:
        bp_status = "Normal" if latest_bp.systolic <= 120 else "Elevated"
        lines.append(f"💓 BP: {latest_bp.systolic}/{latest_bp.diastolic} mmHg ({bp_status})")
    
    if latest_sugar:
        sugar_status = "Normal" if latest_sugar.fasting_glucose < 100 else "High"
        lines.append(f"🩸 Sugar: {latest_sugar.fasting_glucose} mg/dL ({sugar_status})")
    
    if latest_bp or latest_sugar:
        lines.append("")
    
    # Add top 3 recommendations
    if care_items:
        lines.append("📋 *Top Health Tips:*")
        for idx, item in enumerate(care_items[:3], 1):
            # Get first prevention step
            import json
            steps = json.loads(item.prevention_steps) if item.prevention_steps else []
            if steps:
                lines.append(f"{idx}. {steps[0]}")
        lines.append("")
    
    lines.append("📱 Track your health with VitalID")
    lines.append("🔗 https://vitalid.health")
    
    message = "\n".join(lines)
    
    # Generate WhatsApp URL (escape special characters)
    import urllib.parse
    encoded_message = urllib.parse.quote(message)
    whatsapp_url = f"https://wa.me/?text={encoded_message}"
    
    return {
        "message": message,
        "whatsapp_url": whatsapp_url,
        "sms_text": message.replace("*", "").replace("_", ""),  # Remove markdown for SMS
        "user_name": user.full_name,
        "health_id": user.health_id
    }


@router.get("/whatsapp-link")
async def get_whatsapp_share_link(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get direct WhatsApp share link"""
    summary = await get_shareable_summary(user_id, db)
    return {"url": summary.get("whatsapp_url", "")}
