import os
import json
import hashlib
import httpx
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
    """Attempt a real Polygon Amoy transaction; fall back to mock if keys missing."""
    private_key = os.getenv("OWNER_PRIVATE_KEY")

    if not private_key:
        return _mock_tx(data_hash)

    try:
        from web3 import Web3
        rpc_url = os.getenv("POLYGON_RPC_URL", "https://rpc-amoy.polygon.technology/")
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        account = w3.eth.account.from_key(private_key)
        tx = {
            "nonce": w3.eth.get_transaction_count(account.address),
            "to": account.address,
            "value": 0,
            "gas": 50000,
            "gasPrice": w3.eth.gas_price,
            "data": w3.to_hex(text=data_hash),
            "chainId": 80002,  # Polygon Amoy chain ID
        }
        signed = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        return w3.to_hex(tx_hash)
    except Exception as e:
        print(f"Blockchain tx error: {e}")
        return _mock_tx(data_hash)


async def verify_tx_on_polygonscan(tx_hash: str) -> dict:
    """Verify a transaction on Polygon Amoy via PolygonScan API."""
    if tx_hash.startswith("0xmock_"):
        return {"verified": False, "reason": "Mock transaction — add OWNER_PRIVATE_KEY to go live"}

    api_key = os.getenv("POLYGONSCAN_API_KEY", "")
    url = "https://api-amoy.polygonscan.com/api"
    params = {
        "module": "transaction",
        "action": "gettxreceiptstatus",
        "txhash": tx_hash,
        "apikey": api_key,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            data = resp.json()
            status = data.get("result", {}).get("status", "")
            return {
                "verified": status == "1",
                "status": status,
                "explorer_url": f"https://amoy.polygonscan.com/tx/{tx_hash}",
            }
    except Exception as e:
        return {"verified": False, "reason": str(e)}


async def record_on_chain(
    db: AsyncSession,
    user_id: str,
    record_type: str,
    payload: dict,
    summary: str,
    record_date: date = None,
) -> BlockchainRecord:
    """Hash the payload, push to Polygon (or mock), persist a BlockchainRecord row."""
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


# Legacy helper
async def mint_health_record(health_id: str, file_url: str, extracted_data: dict) -> str:
    data_hash = _make_hash({"health_id": health_id, "file_url": file_url, "data": extracted_data})
    return await _polygon_tx(data_hash)
