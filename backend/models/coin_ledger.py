"""
Coin ledger model — tracks all coin transactions with blockchain TX hashes.
"""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from database import Base


class CoinLedger(Base):
    __tablename__ = "coin_ledger"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Integer, nullable=False)  # positive=earned, negative=redeemed
    activity_type = Column(String(50), nullable=False)  # LOG_BP, CLINIC_VISIT, REDEEM, etc.
    tx_hash = Column(String(100), nullable=True)  # blockchain transaction hash
    blockchain_confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ─── Pydantic Schemas ───

class CoinTransaction(BaseModel):
    id: str
    amount: int
    activity_type: str
    tx_hash: Optional[str] = None
    blockchain_confirmed: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class CoinBalance(BaseModel):
    total_balance: int
    earned_today: int
    daily_limit: int = 50
    transactions: list[CoinTransaction] = []
