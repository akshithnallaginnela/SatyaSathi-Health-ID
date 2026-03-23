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
    return {"balance": balance}

@router.get("/offers")
async def get_offers():
    """Return mock offers for coin redemption."""
    return [
        {"id": "o1", "title": "Free Clinic Mini-Checkup", "cost": 500, "description": "Get a free BP and blood sugar checkup at any partner clinic."},
        {"id": "o2", "title": "Rs 100 Pharmacy Voucher", "cost": 1000, "description": "Flat discount on your next medicine purchase."},
        {"id": "o3", "title": "Premium Diet Plan (1 Month)", "cost": 2500, "description": "Expert personalized diet consultation."},
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
