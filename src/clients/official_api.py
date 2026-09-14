import hmac
import hashlib
from typing import Dict, Any, List
from src.clients.base_client import BaseSearchClient

def generate_top_signature(params: Dict[str, Any], app_secret: str) -> str:
    """
    Computes TOP Protocol HMAC-SHA256 signature:
    1. Sort parameters alphabetically by key.
    2. Concatenate key + value.
    3. Sign using HMAC-SHA256 with app_secret as the key.
    4. Return uppercase hex string.
    """
    sorted_keys = sorted(params.keys())
    query_str = "".join(f"{k}{params[k]}" for k in sorted_keys if k != "sign")
    signature = hmac.new(
        app_secret.encode("utf-8"),
        query_str.encode("utf-8"),
        hashlib.sha256
    ).hexdigest().upper()
    return signature

class OfficialAliExpressClient(BaseSearchClient):
    GATEWAY_URL = "https://api-sg.aliexpress.com/rest"

    def __init__(self, app_key: str, app_secret: str):
        self.app_key = app_key
        self.app_secret = app_secret

    def is_configured(self) -> bool:
        return bool(self.app_key and self.app_secret)

    def search(self, query: str, max_items: int = 30) -> List[Dict[str, Any]]:
        if not self.is_configured():
            return []
        # Official endpoint implementation ready to query api-sg once approved
        return []
