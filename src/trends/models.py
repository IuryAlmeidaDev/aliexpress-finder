"""Data models for the Trend Radar pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

STRATEGY_OCEANO_AZUL = "OCEANO_AZUL"
STRATEGY_TENDENCIA = "TENDENCIA"
STRATEGY_EMERGENTE = "EMERGENTE"
STRATEGY_SATURADO = "SATURADO"
STRATEGY_PENDENTE = "PENDENTE"


@dataclass
class TrendTerm:
    id: int
    term: str
    category: str
    source: str  # 'ali', 'alibaba', 'both'
    active: bool
    created_at: str
    last_hit_at: Optional[str] = None


@dataclass
class TrendSnapshot:
    id: int
    term_id: int
    source: str  # 'aliexpress' or 'alibaba'
    product_id: str
    title: str
    price_brl: Optional[float]
    price_usd: Optional[float]
    sales_total: Optional[int]
    rating: Optional[float]
    moq: Optional[int]
    supplier_name: Optional[str]
    is_verified: Optional[bool]
    url: str
    collected_at: str


@dataclass
class TrendVelocity:
    product_id: str
    source: str
    title: str
    url: str
    category: str
    price_brl: Optional[float]
    sales_total: Optional[int]
    sales_velocity_7d: int
    sales_velocity_30d: int
    acceleration: float  # % change week-over-week
    rating: Optional[float] = None
    moq: Optional[int] = None
    supplier_name: Optional[str] = None
    is_verified: Optional[bool] = None


@dataclass
class TrendOpportunity:
    product_id: str
    source: str
    title: str
    url: str
    category: str
    price_brl: Optional[float]
    sales_total: Optional[int]
    sales_velocity_7d: int
    sales_velocity_30d: int
    acceleration: float
    ml_query: str
    ml_competitors: Optional[int]
    ml_avg_price: Optional[float]
    ml_min_price: Optional[float]
    ml_full_share_pct: Optional[float]
    ml_total_sales_br: Optional[int]
    landed_cost_brl: Optional[float]
    suggested_price_brl: Optional[float]
    net_margin_pct: Optional[float]
    strategy: str
    trend_score: float
    supplier_name: Optional[str] = None
    moq: Optional[int] = None
    is_verified: Optional[bool] = None
    sparkline: list[int] = field(default_factory=list)
    calculated_at: str = ""
