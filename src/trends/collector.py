"""Stage 1: Daily collection of China marketplace data for trend tracking."""
from __future__ import annotations

import logging
import random
import time
from datetime import datetime, timezone

from src.clients.direct_scraper import DirectAliExpressClient
from src.clients.alibaba_scraper import DirectAlibabaClient
from src.finance.currency import get_usd_brl_rate
from src.config import load_config
from .repository import TrendRepository

logger = logging.getLogger(__name__)

BLOCK_SIZE = 15
BLOCK_PAUSE_SECONDS = 600  # 10 minutes
REQUEST_DELAY_RANGE = (2.0, 5.0)
ITEMS_PER_TERM = 20


def collect_trends(
    repo: TrendRepository,
    block_pause: float | None = None,
    request_delay: tuple[float, float] | None = None,
) -> dict:
    """Run Stage 1: scrape China sources for all active terms.

    Returns dict with keys: collected, skipped_terms, blocked.
    """
    pause = block_pause if block_pause is not None else BLOCK_PAUSE_SECONDS
    delay = request_delay if request_delay is not None else REQUEST_DELAY_RANGE

    terms = repo.get_active_terms()
    if not terms:
        logger.warning("No active terms found. Run seed_default_terms() first.")
        return {"collected": 0, "skipped_terms": 0, "blocked": False}

    cfg = load_config()
    rate_info = get_usd_brl_rate(fallback_rate=cfg.DEFAULT_USD_BRL)
    usd_rate = rate_info.rate

    ali_client = DirectAliExpressClient()
    baba_client = DirectAlibabaClient()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    total_collected = 0
    skipped_terms = 0
    blocked = False

    for block_start in range(0, len(terms), BLOCK_SIZE):
        block = terms[block_start:block_start + BLOCK_SIZE]
        logger.info(f"Processing block {block_start // BLOCK_SIZE + 1} "
                     f"({len(block)} terms)")

        for term in block:
            snapshots: list[dict] = []

            # AliExpress
            if term.source in ("ali", "both"):
                try:
                    if delay[1] > 0:
                        time.sleep(random.uniform(delay[0], delay[1]))
                    items = ali_client.search(term.term, limit=ITEMS_PER_TERM)
                    for item in items:
                        snapshots.append({
                            "term_id": term.id,
                            "source": "aliexpress",
                            "product_id": str(item.get("id", "")),
                            "title": item.get("title", ""),
                            "price_brl": item.get("price"),
                            "price_usd": (item["price"] / usd_rate
                                          if item.get("price") else None),
                            "sales_total": item.get("sales"),
                            "rating": item.get("rating"),
                            "moq": None,
                            "supplier_name": None,
                            "is_verified": None,
                            "url": item.get("url", ""),
                            "collected_at": today,
                        })
                except Exception as e:
                    logger.warning(f"AliExpress failed for '{term.term}': {e}")
                    skipped_terms += 1

            # Alibaba
            if term.source in ("alibaba", "both"):
                try:
                    if delay[1] > 0:
                        time.sleep(random.uniform(delay[0], delay[1]))
                    items = baba_client.search(term.term, limit=ITEMS_PER_TERM)
                    for item in items:
                        price_brl = item.get("price", 0)
                        snapshots.append({
                            "term_id": term.id,
                            "source": "alibaba",
                            "product_id": str(item.get("id", "")),
                            "title": item.get("title", ""),
                            "price_brl": price_brl,
                            "price_usd": (price_brl / usd_rate
                                          if price_brl else None),
                            "sales_total": item.get("sales"),
                            "rating": item.get("rating"),
                            "moq": item.get("moq"),
                            "supplier_name": item.get("supplier_name"),
                            "is_verified": item.get("is_verified"),
                            "url": item.get("url", ""),
                            "collected_at": today,
                        })
                except Exception as e:
                    logger.warning(f"Alibaba failed for '{term.term}': {e}")
                    skipped_terms += 1

            if snapshots:
                repo.save_snapshots(snapshots)
                total_collected += len(snapshots)

        # Pause between blocks (except after last block)
        if block_start + BLOCK_SIZE < len(terms) and pause > 0:
            logger.info(f"Block pause: sleeping {pause}s")
            time.sleep(pause)

    logger.info(f"Collection complete: {total_collected} snapshots, "
                f"{skipped_terms} skipped terms")
    return {"collected": total_collected, "skipped_terms": skipped_terms,
            "blocked": blocked}
