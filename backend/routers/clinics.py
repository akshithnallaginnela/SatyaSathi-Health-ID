from fastapi import APIRouter
import os
import requests
from datetime import datetime, date
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import Depends, HTTPException

from database import get_db
from security.jwt_handler import get_current_user_id
from models.coin_ledger import CoinLedger

router = APIRouter(prefix="/api/clinics", tags=["Clinics Near Me"])


class ClinicCheckInRequest(BaseModel):
    clinic_name: str
    qr_payload: str | None = None


@router.post("/check-in")
async def clinic_check_in(
    data: ClinicCheckInRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Validate clinic check-in (MVP) and reward coins once per day.
    For production, verify signed QR payload from partner clinics.
    """
    if not data.clinic_name.strip():
        raise HTTPException(status_code=400, detail="clinic_name is required.")

    today_start = datetime.combine(date.today(), datetime.min.time())
    already_checked_in = await db.execute(
        select(func.count())
        .select_from(CoinLedger)
        .where(
            CoinLedger.user_id == user_id,
            CoinLedger.activity_type == "CLINIC_VISIT",
            CoinLedger.created_at >= today_start,
        )
    )
    if (already_checked_in.scalar() or 0) > 0:
        raise HTTPException(status_code=400, detail="Clinic check-in reward already claimed today.")

    reward = 50
    db.add(
        CoinLedger(
            user_id=user_id,
            amount=reward,
            activity_type="CLINIC_VISIT",
        )
    )
    await db.flush()

    balance_result = await db.execute(
        select(func.coalesce(func.sum(CoinLedger.amount), 0)).where(CoinLedger.user_id == user_id)
    )
    balance = int(balance_result.scalar() or 0)

    return {
        "message": f"Check-in recorded at {data.clinic_name}.",
        "coins_earned": reward,
        "total_balance": balance,
    }

@router.get("/nearest")
async def get_nearest_clinics(lat: float, lng: float):
    """
    Fetches the nearest clinics/hospitals from Google Places API.
    Uses mock data if GOOGLE_MAPS_API_KEY is not defined.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print("WARNING: GOOGLE_MAPS_API_KEY missing. Returning mock clinics.")
        return [
            {"name": "City Health Clinic", "distance": "1.2 km", "type": "Dr. Sharma • General Physician"},
            {"name": "HeartCare Center", "distance": "3.5 km", "type": "Dr. Patel • Cardiologist"}
        ]
        
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=5000&type=hospital&key={api_key}"
    resp = requests.get(url)
    
    if resp.ok:
        data = resp.json()
        clinics = []
        for p in data.get("results", [])[:5]:
            clinics.append({
                "name": p.get("name"),
                "distance": "Nearby (Requires Matrix API)",  # Just a placeholder for distance
                "type": p.get("vicinity") or "Healthcare Facility"
            })
        return clinics
        
    return {"error": "Failed to fetch from Google Maps API."}
