import os
import json
import hashlib
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession

from models.domain import BlockchainRecord


def _make_hash(payload: dict) -> str:
    """SHA-256 hash of a deterministically serialised payload."""
    dumped = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(dumped).hexdigest()


def _mock_tx(data_hash: str) -> str:
    return f"0xmock_{data_hash[:40]}"


async def _polygon_tx(data_hash: str) -> str:
    """Attempt a real Polygon transaction; fall back to mock if keys missing."""
    private_key = os.getenv("OWNER_PRIVATE_KEY")
    contract_address = os.getenv("CONTRACT_ADDRESS")

    if not private_key:
        return _mock_tx(data_hash)

    try:
        from web3 import Web3
        rpc_url = os.getenv("POLYGON_RPC_URL", "https://rpc-amoy.polygon.technology/")
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        account = w3.eth.account.from_key(private_key)
        tx = {
            "nonce": w3.eth.get_transaction_count(account.address),
            "to": contract_address if contract_address else account.address,
            "value": 0,
            "gas": 100000,
            "maxFeePerGas": w3.to_wei("30", "gwei"),
            "maxPriorityFeePerGas": w3.to_wei("30", "gwei"),
            "data": w3.to_hex(text=data_hash),
            "chainId": w3.eth.chain_id,
        }
        signed = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        return w3.to_hex(tx_hash)
    except Exception as e:
        print(f"Blockchain tx error: {e}")
        return _mock_tx(data_hash)


async def record_on_chain(
    db: AsyncSession,
    user_id: str,
    record_type: str,       # "BP" | "SUGAR" | "BMI" | "REPORT"
    payload: dict,          # the data being anchored
    summary: str,           # human-readable e.g. "BP: 120/80 mmHg"
    record_date: date = None,
) -> BlockchainRecord:
    """
    Hash the payload, push to Polygon (or mock), and persist a BlockchainRecord row.
    Returns the saved record.
    """
    if record_date is None:
        record_date = date.today()

    data_hash = _make_hash({**payload, "user_id": user_id, "record_type": record_type})
    tx_hash = await _polygon_tx(data_hash)

    record = BlockchainRecord(
        user_id=user_id,
        record_type=record_type,
        record_date=record_date,
        data_hash=data_hash,
        tx_hash=tx_hash,
        summary=summary,
    )
    db.add(record)
    print(f"⛓  Blockchain record: {record_type} | {summary} | tx={tx_hash[:20]}...")
    return record


# Legacy helper kept for backward compat
async def mint_health_record(health_id: str, file_url: str, extracted_data: dict) -> str:
    data_hash = _make_hash({"health_id": health_id, "file_url": file_url, "data": extracted_data})
    return await _polygon_tx(data_hash)
