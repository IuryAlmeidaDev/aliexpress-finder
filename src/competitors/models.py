from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class TargetProduct:
    """Represents the benchmark product being investigated."""
    title: str
    reference_price_brl: float
    clean_query: str
    url: Optional[str] = None
    category: str = "Geral"
    specs: Dict[str, Any] = field(default_factory=dict)
    kit_items: List[str] = field(default_factory=list)

@dataclass
class CompetitorProduct:
    """Represents an active competitor offering in the domestic market."""
    title: str
    url: str
    store_name: str
    platform: str
    price_brl: float
    original_price_brl: Optional[float] = None
    shipping_type: str = "Normal"
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    sales_volume: Optional[str] = None
    kit_items: List[str] = field(default_factory=list)
    differentials: List[str] = field(default_factory=list)

@dataclass
class MarketDossier:
    """Complete benchmarking and strategic dossier for a niche/product."""
    target: TargetProduct
    competitors: List[CompetitorProduct] = field(default_factory=list)
    min_competitor_price: float = 0.0
    max_competitor_price: float = 0.0
    avg_competitor_price: float = 0.0
    median_competitor_price: float = 0.0
    full_shipping_share_pct: float = 0.0
    common_kit_items: List[str] = field(default_factory=list)
    market_gaps: List[str] = field(default_factory=list)
    target_fob_china_usd: float = 0.0
    recommended_china_suppliers: List[Dict[str, Any]] = field(default_factory=list)
