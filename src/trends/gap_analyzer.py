"""Stage 3: Cross-reference trending China products with Brazilian market gaps."""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

from src.competitors.radar import CompetitorRadar
from src.finance.currency import get_usd_brl_rate
from src.config import load_config
from .models import TrendVelocity, TrendOpportunity, STRATEGY_PENDENTE
from .repository import TrendRepository
from .scoring import calculate_trend_score

logger = logging.getLogger(__name__)

MAX_GAP_ANALYSIS = 100

# Extended translation map for trend titles
TREND_TRANSLATION_MAP = {
    "wireless": "sem fio", "earbuds": "fone", "bluetooth": "bluetooth",
    "charger": "carregador", "portable": "portátil", "smart": "inteligente",
    "watch": "relógio", "speaker": "caixa de som", "light": "luz",
    "projector": "projetor", "kitchen": "cozinha", "organizer": "organizador",
    "storage": "armazenamento", "mold": "molde", "silicone": "silicone",
    "blender": "liquidificador", "vacuum": "vácuo", "sealer": "seladora",
    "coffee": "café", "hair": "cabelo", "straightener": "alisador",
    "brush": "escova", "facial": "facial", "massager": "massageador",
    "nail": "unha", "makeup": "maquiagem", "teeth": "dentes",
    "whitening": "clareamento", "scalp": "couro cabeludo", "beauty": "beleza",
    "sunglasses": "óculos de sol", "polarized": "polarizado", "automatic": "automático",
    "bag": "bolsa", "wallet": "carteira", "ring": "anel", "scarf": "lenço",
    "hat": "chapéu", "level": "nível", "laser": "laser", "screwdriver": "parafusadeira",
    "soldering": "solda", "caliper": "paquímetro", "digital": "digital",
    "heat": "calor", "gun": "pistola", "wire": "fio", "stripper": "descascador",
    "multimeter": "multímetro", "pet": "pet", "feeder": "alimentador",
    "dog": "cachorro", "harness": "peitoral", "cat": "gato", "toy": "brinquedo",
    "grooming": "tosa", "training": "adestramento", "collar": "coleira",
    "water": "água", "fountain": "fonte", "resistance": "resistência",
    "bands": "faixas", "jump": "pular", "rope": "corda", "hiking": "trilha",
    "backpack": "mochila", "camping": "camping", "yoga": "yoga", "mat": "tapete",
    "fishing": "pesca", "lure": "isca", "bike": "bicicleta", "baby": "bebê",
    "carrier": "canguru", "educational": "educativo", "kids": "infantil",
    "tablet": "tablet", "monitor": "monitor", "stroller": "carrinho",
    "teething": "mordedor",
}

STOP_WORDS = {
    "hot", "selling", "new", "2024", "2025", "2026", "factory", "wholesale",
    "oem", "odm", "free", "shipping", "drop", "dropshipping", "high", "quality",
    "best", "top", "pro", "premium", "original", "genuine", "brand",
    "for", "with", "and", "the", "set", "kit", "pcs", "lot", "pack",
}


def _translate_title(title: str) -> str:
    """Translate an English product title to Portuguese search query."""
    words = title.lower().split()
    translated = []
    for word in words:
        clean = word.strip(".,;:!?()[]{}\"'")
        if clean in STOP_WORDS or not clean:
            continue
        if clean in TREND_TRANSLATION_MAP:
            translated.append(TREND_TRANSLATION_MAP[clean])
        elif len(clean) > 2:
            translated.append(clean)
    return " ".join(translated[:6])  # limit to 6 words for search


def _safe_int(val: object) -> int:
    if isinstance(val, int):
        return val
    if isinstance(val, float):
        return int(val)
    if isinstance(val, str):
        digits = re.findall(r"\d+", val.replace(".", "").replace(",", ""))
        if digits:
            return int("".join(digits))
    return 0


def analyze_gaps(
    velocities: list[TrendVelocity],
    repo: TrendRepository,
) -> list[TrendOpportunity]:
    """Run Stage 3: cross-reference trending products with Mercado Livre."""
    top = velocities[:MAX_GAP_ANALYSIS]
    if not top:
        return []

    cfg = load_config()
    rate_info = get_usd_brl_rate(fallback_rate=cfg.DEFAULT_USD_BRL)
    usd_rate = rate_info.rate

    radar = CompetitorRadar()
    now = datetime.now(timezone.utc).isoformat()

    # Pre-compute max velocity per category for scoring
    max_vel_by_cat: dict[str, int] = {}
    for v in velocities:
        cur = max_vel_by_cat.get(v.category, 0)
        if v.sales_velocity_7d > cur:
            max_vel_by_cat[v.category] = v.sales_velocity_7d

    opportunities: list[TrendOpportunity] = []

    for v in top:
        ml_query = _translate_title(v.title)
        ml_competitors = None
        ml_avg_price = None
        ml_min_price = None
        ml_full_share_pct = None
        ml_total_sales_br = None
        landed_cost = None
        suggested_price = None
        net_margin = None

        try:
            competitors = radar.find_competitors(ml_query, limit=5)
            ml_competitors = len(competitors)

            if competitors:
                prices = [c.price_brl for c in competitors if isinstance(getattr(c, 'price_brl', None), (int, float)) and c.price_brl > 0]
                ml_avg_price = sum(prices) / len(prices) if prices else 0.0
                ml_min_price = min(prices) if prices else 0.0
                full_count = sum(1 for c in competitors
                                 if getattr(c, 'shipping_type', '') == 'Full')
                ml_full_share_pct = (full_count / len(competitors)) * 100 if competitors else 0.0
                ml_total_sales_br = sum(
                    _safe_int(getattr(c, 'sales_volume', 0)) for c in competitors
                )
            else:
                ml_avg_price = 0.0
                ml_min_price = 0.0
                ml_full_share_pct = 0.0
                ml_total_sales_br = 0

        except Exception as e:
            logger.warning(f"Gap analysis failed for '{v.title}': {e}")

        # Calculate landed cost
        if v.price_brl and v.price_brl > 0:
            fob = v.price_brl
            freight = fob * 0.15
            customs_base = fob + freight
            import_tax = customs_base * 0.60
            icms_base = (customs_base + import_tax) / (1.0 - cfg.DEFAULT_ICMS_RATE)
            icms = icms_base * cfg.DEFAULT_ICMS_RATE
            landed_cost = round(customs_base + import_tax + icms, 2)

            # Suggested price
            if ml_avg_price and ml_avg_price > 0:
                suggested_price = ml_avg_price
            else:
                suggested_price = round(landed_cost / (1.0 - cfg.DEFAULT_TARGET_MARGIN), 2)

            ml_fee = suggested_price * cfg.DEFAULT_MARKETPLACE_FEE
            net_profit = suggested_price - ml_fee - landed_cost
            net_margin = round((net_profit / suggested_price) * 100, 1) if suggested_price > 0 else 0.0

        # Score and classify
        max_vel = max_vel_by_cat.get(v.category, v.sales_velocity_7d)
        score, strategy = calculate_trend_score(
            v, ml_competitors=ml_competitors,
            net_margin_pct=net_margin, max_velocity_in_category=max_vel
        )

        sparkline = repo.get_sparkline(v.product_id, v.source, points=30)

        # Get snapshot_id for the latest snapshot
        snapshot_id = repo.get_latest_snapshot_id(v.product_id, v.source) or 0

        opp = TrendOpportunity(
            product_id=v.product_id, source=v.source, title=v.title,
            url=v.url, category=v.category, price_brl=v.price_brl,
            sales_total=v.sales_total, sales_velocity_7d=v.sales_velocity_7d,
            sales_velocity_30d=v.sales_velocity_30d, acceleration=v.acceleration,
            ml_query=ml_query, ml_competitors=ml_competitors,
            ml_avg_price=ml_avg_price, ml_min_price=ml_min_price,
            ml_full_share_pct=ml_full_share_pct, ml_total_sales_br=ml_total_sales_br,
            landed_cost_brl=landed_cost, suggested_price_brl=suggested_price,
            net_margin_pct=net_margin, strategy=strategy, trend_score=score,
            supplier_name=v.supplier_name, moq=v.moq, is_verified=v.is_verified,
            sparkline=sparkline, calculated_at=now,
        )
        opportunities.append(opp)

        # Save to database
        repo.save_opportunities([{
            "snapshot_id": snapshot_id,
            "product_id": v.product_id, "source": v.source,
            "sales_velocity_7d": v.sales_velocity_7d,
            "sales_velocity_30d": v.sales_velocity_30d,
            "acceleration": v.acceleration,
            "ml_query": ml_query, "ml_competitors": ml_competitors,
            "ml_avg_price": ml_avg_price, "ml_min_price": ml_min_price,
            "ml_full_share_pct": ml_full_share_pct,
            "ml_total_sales_br": ml_total_sales_br,
            "landed_cost_brl": landed_cost,
            "suggested_price_brl": suggested_price,
            "net_margin_pct": net_margin,
            "strategy": strategy, "trend_score": score,
            "calculated_at": now,
        }])

    opportunities.sort(key=lambda o: o.trend_score, reverse=True)
    return opportunities
