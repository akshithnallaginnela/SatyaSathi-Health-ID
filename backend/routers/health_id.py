"""
Health ID Card API — Generate QR code with emergency health info
"""
import io
import base64
import json
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import qrcode
from PIL import Image, ImageDraw, ImageFont

from database import get_db
from models.domain import User, BPReading, SugarReading, BloodReport
from security.jwt_handler import get_current_user_id

router = APIRouter(prefix="/api/health-id", tags=["Health ID"])


@router.get("/card-data")
async def get_health_id_data(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get data for health ID card"""
    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
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
    
    # Get latest blood report
    report_result = await db.execute(
        select(BloodReport).where(BloodReport.user_id == user_id)
        .order_by(desc(BloodReport.uploaded_at)).limit(1)
    )
    latest_report = report_result.scalar_one_or_none()
    
    # Build emergency data
    emergency_data = {
        "health_id": user.health_id,
        "name": user.full_name,
        "age": None,
        "gender": user.gender,
        "blood_group": getattr(user, 'blood_group', None),
        "has_bp": latest_bp is not None,
        "bp_value": f"{latest_bp.systolic}/{latest_bp.diastolic}" if latest_bp else None,
        "bp_date": latest_bp.measured_at.strftime("%Y-%m-%d") if latest_bp else None,
        "has_sugar": latest_sugar is not None,
        "sugar_value": f"{latest_sugar.fasting_glucose}" if latest_sugar else None,
        "sugar_date": latest_sugar.measured_at.strftime("%Y-%m-%d") if latest_sugar else None,
        "has_report": latest_report is not None,
        "report_date": latest_report.uploaded_at.strftime("%Y-%m-%d") if latest_report else None,
        "hemoglobin": latest_report.hemoglobin if latest_report else None,
        "last_clinic_visit": None,  # TODO: Add clinic visit tracking
        "emergency_contact": getattr(user, 'emergency_contact', None) or user.phone_number,
        "qr_url": f"https://vitalid.health/emergency/{user.health_id}"
    }
    
    # Calculate age
    if user.date_of_birth:
        today = date.today()
        dob = user.date_of_birth
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        emergency_data["age"] = age
    
    return emergency_data


@router.get("/qr-code")
async def generate_qr_code(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Generate QR code embedding real health data as JSON — no URL, works offline."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get latest vitals
    bp_res = await db.execute(select(BPReading).where(BPReading.user_id == user_id).order_by(desc(BPReading.measured_at)).limit(1))
    latest_bp = bp_res.scalar_one_or_none()
    sugar_res = await db.execute(select(SugarReading).where(SugarReading.user_id == user_id).order_by(desc(SugarReading.measured_at)).limit(1))
    latest_sugar = sugar_res.scalar_one_or_none()
    report_res = await db.execute(select(BloodReport).where(BloodReport.user_id == user_id).order_by(desc(BloodReport.uploaded_at)).limit(1))
    latest_report = report_res.scalar_one_or_none()

    # Build risk flags from vitals
    risks = []
    if latest_bp and latest_bp.systolic >= 140:
        risks.append("Hypertension")
    elif latest_bp and latest_bp.systolic >= 130:
        risks.append("Pre-hypertension")
    if latest_sugar and latest_sugar.fasting_glucose >= 126:
        risks.append("Diabetes")
    elif latest_sugar and latest_sugar.fasting_glucose >= 100:
        risks.append("Pre-diabetes")
    if latest_report and latest_report.hemoglobin:
        hb_low = 13.5 if (user.gender or '').lower() == 'male' else 12.0
        if float(latest_report.hemoglobin) < hb_low:
            risks.append("Anemia")

    # Compact JSON — no URL, pure data
    qr_data = {
        "id":   user.health_id,
        "name": user.full_name,
        "bg":   getattr(user, 'blood_group', None) or "Unknown",
        "bp":   f"{latest_bp.systolic}/{latest_bp.diastolic}" if latest_bp else None,
        "glu":  str(latest_sugar.fasting_glucose) if latest_sugar else None,
        "hb":   str(latest_report.hemoglobin) if latest_report and latest_report.hemoglobin else None,
        "risk": risks,
        "ec":   getattr(user, 'emergency_contact', None) or user.phone_number,
    }

    qr = qrcode.QRCode(version=2, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=2)
    qr.add_data(json.dumps(qr_data, separators=(',', ':')))
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1A3A38", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


@router.get("/download-card")
async def download_health_card(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Generate downloadable health ID card image"""
    # Get user data
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get latest vitals
    bp_result = await db.execute(
        select(BPReading).where(BPReading.user_id == user_id)
        .order_by(desc(BPReading.measured_at)).limit(1)
    )
    latest_bp = bp_result.scalar_one_or_none()
    
    sugar_result = await db.execute(
        select(SugarReading).where(SugarReading.user_id == user_id)
        .order_by(desc(SugarReading.measured_at)).limit(1)
    )
    latest_sugar = sugar_result.scalar_one_or_none()
    
    # Create card image (800x500px)
    card = Image.new('RGB', (800, 500), color='white')
    draw = ImageDraw.Draw(card)
    
    # Draw header background
    draw.rectangle([(0, 0), (800, 120)], fill='#26C6BF')
    
    # Add text (using default font - in production use custom fonts)
    # Title
    draw.text((30, 30), "VitalID Health Card", fill='white', font=None)
    draw.text((30, 60), user.health_id, fill='white', font=None)
    
    # User info
    draw.text((30, 150), f"Name: {user.full_name}", fill='#333333', font=None)
    if user.date_of_birth:
        age = date.today().year - user.date_of_birth.year
        draw.text((30, 180), f"Age: {age} | Gender: {user.gender or 'N/A'}", fill='#666666', font=None)
    
    # Vitals
    y_pos = 220
    if latest_bp:
        draw.text((30, y_pos), f"BP: {latest_bp.systolic}/{latest_bp.diastolic} mmHg", fill='#333333', font=None)
        y_pos += 30
    if latest_sugar:
        draw.text((30, y_pos), f"Sugar: {latest_sugar.fasting_glucose} mg/dL", fill='#333333', font=None)
        y_pos += 30
    
    draw.text((30, y_pos), f"Blood Group: {getattr(user, 'blood_group', 'Not set')}", fill='#333333', font=None)
    
    # Generate QR code
    qr_data = {"id": user.health_id, "url": f"https://vitalid.health/emergency/{user.health_id}"}
    qr = qrcode.QRCode(version=1, box_size=5, border=1)
    qr.add_data(json.dumps(qr_data))
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#26C6BF", back_color="white")
    qr_img = qr_img.resize((150, 150))
    
    # Paste QR code on card
    card.paste(qr_img, (620, 150))
    
    # Add footer
    draw.text((30, 460), "Emergency Contact: " + user.phone_number, fill='#999999', font=None)
    
    # Convert to bytes
    buf = io.BytesIO()
    card.save(buf, format='PNG')
    buf.seek(0)
    
    return StreamingResponse(
        buf,
        media_type="image/png",
        headers={"Content-Disposition": f"attachment; filename=vitalid_{user.health_id}.png"}
    )
