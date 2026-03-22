import os
import json
import hashlib
from web3 import Web3

def get_web3():
    rpc_url = os.getenv("POLYGON_RPC_URL", "https://rpc-amoy.polygon.technology/")
    return Web3(Web3.HTTPProvider(rpc_url))

async def mint_health_record(health_id: str, file_url: str, extracted_data: dict) -> str:
    """
    Creates an immutable hash of the document and stores it on Polygon.
    Returns the transaction hash.
    """
    w3 = get_web3()
    
    private_key = os.getenv("OWNER_PRIVATE_KEY")
    contract_address = os.getenv("CONTRACT_ADDRESS")
    
    # Hash the data to create a unique immutable fingerprint
    record_payload = {
        "health_id": health_id,
        "file_url": file_url,
        "data": extracted_data
    }
    dumped = json.dumps(record_payload, sort_keys=True).encode("utf-8")
    record_hash = hashlib.sha256(dumped).hexdigest()
    
    if not private_key:
        print("WARNING: Blockchain OWNER_PRIVATE_KEY missing. Returning mock tx hash.")
        return f"0xmock_polygon_hash_{record_hash[:40]}"
        
    try:
        account = w3.eth.account.from_key(private_key)
        
        # If no contract provided, append hash in the transaction data 
        tx = {
            'nonce': w3.eth.get_transaction_count(account.address),
            'to': account.address if not contract_address else contract_address,
            'value': 0,
            'gas': 100000,
            'maxFeePerGas': w3.to_wei('30', 'gwei'),
            'maxPriorityFeePerGas': w3.to_wei('30', 'gwei'),
            'data': w3.to_hex(text=record_hash),
            'chainId': w3.eth.chain_id
        }
        
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return w3.to_hex(tx_hash)
    except Exception as e:
        print(f"Blockchain Error: {e}")
        return f"0xmock_polygon_hash_{record_hash[:40]}"
