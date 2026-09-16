import json
import os
import time
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


AWESOME_API_URL = "https://economia.awesomeapi.com.br/last/USD-BRL"


@dataclass
class CurrencyRate:
    rate: float
    source: str  # "manual", "api", "cache", "stale_cache", "fallback"
    updated_at: str


def get_usd_brl_rate(
    manual_rate: Optional[float] = None,
    fallback_rate: float = 5.50,
    use_cache: bool = True,
    cache_ttl_seconds: int = 7200,  # 2 hours
    cache_file: str = "data/currency_cache.json",
    timeout: int = 4,
) -> CurrencyRate:
    """
    Obtém a taxa de câmbio USD/BRL atualizada.

    Ordem de resolução:
    1. Se `manual_rate` foi informado pelo usuário via CLI (--usd), usa diretamente.
    2. Se `use_cache` for True e o cache local estiver dentro do TTL, usa o cache sem rede.
    3. Consulta a AwesomeAPI em tempo real e atualiza o cache local.
    4. Em caso de falha de rede/timeout:
       a. Se existir cache local anterior (mesmo vencido), usa como `stale_cache`.
       b. Se não existir cache, recorre ao `fallback_rate` (padrão: 5.50).
    """
    now = time.time()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 1. Manual override
    if manual_rate is not None and manual_rate > 0:
        return CurrencyRate(rate=round(float(manual_rate), 4), source="manual", updated_at=now_str)

    # Helper to read cache
    cached_data = None
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
        except Exception:
            cached_data = None

    # 2. Check fresh cache
    if use_cache and cached_data and "rate" in cached_data and "timestamp" in cached_data:
        age = now - cached_data["timestamp"]
        if age <= cache_ttl_seconds:
            return CurrencyRate(
                rate=float(cached_data["rate"]),
                source="cache",
                updated_at=cached_data.get("updated_at", now_str),
            )

    # 3. Fetch from API
    try:
        req = urllib.request.Request(
            AWESOME_API_URL,
            headers={"User-Agent": "AliExpressFinder/1.0"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
            usd_data = payload.get("USDBRL", {})
            bid_rate = float(usd_data.get("bid", 0.0))
            if bid_rate > 0:
                api_updated_at = usd_data.get("create_date", now_str)
                # Persist cache
                os.makedirs(os.path.dirname(os.path.abspath(cache_file)), exist_ok=True)
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "rate": bid_rate,
                            "timestamp": now,
                            "updated_at": api_updated_at,
                        },
                        f,
                        indent=2,
                    )
                return CurrencyRate(rate=bid_rate, source="api", updated_at=api_updated_at)
    except Exception:
        pass

    # 4a. Stale cache fallback
    if cached_data and "rate" in cached_data:
        return CurrencyRate(
            rate=float(cached_data["rate"]),
            source="stale_cache",
            updated_at=cached_data.get("updated_at", now_str),
        )

    # 4b. Hard fallback
    return CurrencyRate(rate=round(float(fallback_rate), 4), source="fallback", updated_at=now_str)
