import requests
from datetime import datetime
from config import ALCHEMY_API_KEY, NETWORK

BASE_URL = f"https://{NETWORK}.g.alchemy.com/v2/{ALCHEMY_API_KEY}"

def get_token_transfers(contract_address, start_block, end_block):
    """Запрашивает токен-трансферы ERC20 контракта."""
    url = f"{BASE_URL}"
    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "alchemy_getAssetTransfers",
        "params": [{
            "fromBlock": hex(start_block),
            "toBlock": hex(end_block),
            "category": ["erc20"],
            "contractAddresses": [contract_address],
            "withMetadata": False,
            "maxCount": "0x3e8"  # ~1000
        }]
    }

    r = requests.post(url, json=payload)
    r.raise_for_status()
    return r.json()["result"]["transfers"]
    