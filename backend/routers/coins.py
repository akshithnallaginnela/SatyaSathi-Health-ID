"""
Coins router — balance, transaction history, and redemption.
"""

from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from pydantic import BaseModel

from database import get_db
from models.coin_ledger import CoinLedger, CoinBalance, CoinTransaction
from security.jwt_handler import get_current_user_id

router = APIRouter(prefix="/api/coins", tags=["Coins"])

MAX_DAILY_COINS = 50

# Mock redemption offers
OFFERS = [
    {"id": "offer_1", "partner": "Netmeds", "offer": "20% off medicines", "coins_required": 100, "category": "medicine"},
    {"id": "offer_2", "partner": "Thyrocare", "offer": "Free CBC test", "coins_required": 200, "category": "lab_test"},
    {"id": "offer_3", "partner": "Cult.fit", "offer": "1 week free gym", "coins_required": 300, "category": "fitness"},
    {"id": "offer_4", "partner": "Pharmacy", "offer": "15% off purchase", "coins_required": 500, "category": "medicine"},
    {"id": "offer_5", "partner": "HealthCheck", "offer": "Full body checkup", "coins_required": 1200, "category": "lab_test"},
]


@router.get("/balance", response_model=CoinBalance)
async def get_balance(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get coin balance and today's earnings."""
    # Total balance
    result = await db.execute(
        select(func.coalesce(func.sum(CoinLedger.amount), 0))
        .where(CoinLedger.user_id == user_id)
    )
    total = result.scalar() or 0

    # Today's earnings
    today_start = datetime.combine(date.today(), datetime.min.time())
    result = await db.execute(
        select(func.coalesce(func.sum(CoinLedger.amount), 0))
        .where(
            CoinLedger.user_id == user_id,
            CoinLedger.created_at >= today_start,
            CoinLedger.amount > 0,
        )
    )
    earned_today = result.scalar() or 0

    # Recent transactions
    result = await db.execute(
        select(CoinLedger)
        .where(CoinLedger.user_id == user_id)
        .order_by(desc(CoinLedger.created_at))
        .limit(20)
    )
    txns = result.scalars().all()

    return CoinBalance(
        total_balance=int(total),
        earned_today=int(earned_today),
        daily_limit=MAX_DAILY_COINS,
        transactions=[CoinTransaction.model_validate(t) for t in txns],
    )


@router.get("/offers")
async def get_offers():
    """Get available redemption offers."""
    return OFFERS


class RedeemRequest(BaseModel):
    offer_id: str


@router.post("/redeem")
async def redeem_coins(
    data: RedeemRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Redeem coins for an offer."""
    offer = next((o for o in OFFERS if o["id"] == data.offer_id), None)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found.")

    # Check balance
    result = await db.execute(
        select(func.coalesce(func.sum(CoinLedger.amount), 0))
        .where(CoinLedger.user_id == user_id)
    )
    balance = result.scalar() or 0

    if balance < offer["coins_required"]:
        raise HTTPException(status_code=400, detail=f"Insufficient coins. Need {offer['coins_required']}, have {balance}.")

    # Deduct coins
    entry = CoinLedger(
        user_id=user_id,
        amount=-offer["coins_required"],
        activity_type="REDEEM",
    )
    db.add(entry)
    await db.flush()

    # Generate mock promo code
    import random, string
    promo = "VID-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

    return {
        "message": f"Redeemed! {offer['offer']} from {offer['partner']}",
        "promo_code": promo,
        "coins_spent": offer["coins_required"],
        "remaining_balance": int(balance - offer["coins_required"]),
    }
