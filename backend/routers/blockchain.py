from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from database import get_db
from models.domain import BlockchainRecord
from security.jwt_handler import get_current_user_id

router = APIRouter(prefix="/api/blockchain", tags=["Blockchain"])

@router.get("/history")
async def get_blockchain_history(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Return the user's immutable health record timeline from the blockchain ledger."""
    result = await db.execute(
        select(BlockchainRecord)
        .where(BlockchainRecord.user_id == user_id)
        .order_by(desc(BlockchainRecord.record_date), desc(BlockchainRecord.created_at))
    )
    records = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "record_type": r.record_type,
            "record_date": str(r.record_date),
            "summary": r.summary,
            "data_hash": r.data_hash,
            "tx_hash": r.tx_hash,
            "is_mock": r.tx_hash.startswith("0xmock_"),
            "created_at": str(r.created_at),
        }
        for r in records
    ]
