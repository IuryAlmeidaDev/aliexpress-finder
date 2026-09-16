from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class ArbitrageItem:
    # China Sourcing (Alibaba / AliExpress)
    source: str                    # "Alibaba" ou "AliExpress"
    china_id: str
    china_title: str
    china_url: str
    china_fob_usd: float           # Unit FOB in USD
    china_fob_brl: float           # Unit FOB in BRL
    moq: int                       # Minimum order quantity
    supplier_name: str
    is_verified: bool              # Verified Supplier flag
    has_trade_assurance: bool      # Trade assurance flag
    china_sales: Optional[int] = None      # Sales volume (AliExpress)
    china_rating: Optional[float] = None   # Rating (AliExpress)

    # Taxes and Landed Cost in Brazil
    import_tax_unit_brl: float = 0.0     # Imposto de Importação 60%
    icms_unit_brl: float = 0.0           # ICMS 17% por dentro
    freight_unit_brl: float = 0.0        # Frete internacional unitário estimado
    landed_cost_unit_brl: float = 0.0    # Custo final unitário desembarcado

    # Domestic Market (Mercado Livre Brasil)
    ml_query: str = ""
    ml_competitors_count: int = 0
    ml_min_price: float = 0.0
    ml_avg_price: float = 0.0
    ml_max_price: float = 0.0
    ml_full_share_pct: float = 0.0
    ml_top_competitor_url: str = ""
    ml_top_competitor_title: str = ""
    ml_avg_rating: Optional[float] = None

    # Unit Economics & Arbitrage
    reference_sale_price_brl: float = 0.0  # Preço de venda base (preço médio ML ou sugerido)
    ml_fee_brl: float = 0.0                # Taxa ML (16%)
    net_profit_brl: float = 0.0            # Lucro líquido em R$
    net_margin_pct: float = 0.0            # Margem líquida %
    roi_pct: float = 0.0                   # ROI sobre custo desembarcado %

    # Strategic Classification
    strategy: str = ""              # "OCEANO_AZUL", "ALTA_MARGEM", "MARCA_PROPRIA", "SATURADO"
    strategy_label: str = ""        # "Oceano Azul", "Alta Margem", "Marca Própria", "Saturado"
    summary: str = ""               # Diagnóstico executivo

@dataclass
class ArbitrageReport:
    query: str
    source: str
    usd_rate: float
    total_scanned: int
    items: List[ArbitrageItem] = field(default_factory=list)
    blue_ocean_count: int = 0
    high_margin_count: int = 0
    private_label_count: int = 0
    saturated_count: int = 0
