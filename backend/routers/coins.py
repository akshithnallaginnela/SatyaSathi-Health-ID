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
    """Return partner offers for coin redemption."""
    return [
        # Diagnostic Centers — 250,000 coins
        {"id": "o1", "partner": "Vijaya Diagnostics", "offer": "Full Body Health Checkup", "coins_required": 250000, "description": "Complete blood panel — CBC, thyroid, liver, kidney & lipids at Vijaya Diagnostics centres."},
        {"id": "o2", "partner": "Vijaya Diagnostics", "offer": "Diabetes Care Package", "coins_required": 250000, "description": "HbA1c, fasting glucose, insulin & lipid profile at Vijaya Diagnostics."},
        # Medical/Pharmacy — 30,000 coins
        {"id": "o3", "partner": "Apollo Pharmacy", "offer": "₹200 Medicine Discount", "coins_required": 30000, "description": "Flat ₹200 off on any medicine purchase at Apollo Pharmacy stores or app."},
        {"id": "o4", "partner": "MedPlus Pharmacy", "offer": "₹150 Medicine Discount", "coins_required": 30000, "description": "₹150 off on medicines and health products at MedPlus stores across India."},
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
