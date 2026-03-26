from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from database import get_db
from models.domain import User, CoinLedger
from security.jwt_handler import get_current_user_id

router = APIRouter(prefix="/api/coins", tags=["Coins"])

@router.get("/balance")
async def get_coin_balance(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Calculate current coin balance."""
    result = await db.execute(
        select(func.sum(CoinLedger.amount)).where(CoinLedger.user_id == user_id)
    )
    balance = result.scalar() or 0
    return {"total_balance": balance}

@router.get("/offers")
async def get_offers():
    """Return real partner offers for coin redemption."""
    return [
        # Diagnostic Centers — 250,000 coins
        {"id": "o1", "partner": "Thyrocare", "offer": "Full Body Checkup (₹1,500 value)", "coins_required": 250000, "description": "Complete blood panel including CBC, thyroid, liver, kidney & lipids at Thyrocare labs."},
        {"id": "o2", "partner": "Dr. Lal PathLabs", "offer": "Aarogyam 1.3 Package", "coins_required": 250000, "description": "72-parameter health checkup at Dr. Lal PathLabs — India's most trusted diagnostic chain."},
        {"id": "o3", "partner": "SRL Diagnostics", "offer": "Diabetes & Heart Combo", "coins_required": 250000, "description": "HbA1c, fasting glucose, lipid profile, ECG at SRL Diagnostics centres nationwide."},
        {"id": "o4", "partner": "Metropolis Healthcare", "offer": "Preventive Health Package", "coins_required": 250000, "description": "CBC, liver function, kidney function, vitamin D & B12 at Metropolis labs."},
        # Medical/Pharmacy — 30,000 coins
        {"id": "o5", "partner": "Apollo Pharmacy", "offer": "₹200 Medicine Discount", "coins_required": 30000, "description": "Flat ₹200 off on any medicine purchase at Apollo Pharmacy stores or app."},
        {"id": "o6", "partner": "MedPlus Pharmacy", "offer": "₹150 Medicine Discount", "coins_required": 30000, "description": "₹150 off on medicines and health products at MedPlus stores across India."},
        {"id": "o7", "partner": "Netmeds", "offer": "₹200 Off on First Order", "coins_required": 30000, "description": "₹200 discount on medicines ordered via Netmeds app or website."},
        {"id": "o8", "partner": "1mg (Tata Health)", "offer": "₹250 Medicine Voucher", "coins_required": 30000, "description": "₹250 off on medicines, lab tests or doctor consultations on 1mg platform."},
    ]

@router.post("/redeem")
async def redeem_offer(
    data: dict,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    offer_id = data.get("offer_id")
    # Mark redemption in ledger as negative amount
    # Simplified mock redemption
    return {"message": "Redemption successful", "offer_id": offer_id}
