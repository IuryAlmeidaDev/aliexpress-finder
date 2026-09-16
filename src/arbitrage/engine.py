import re
import statistics
from typing import List, Dict, Any, Optional
from src.arbitrage.models import ArbitrageItem, ArbitrageReport
from src.competitors.radar import CompetitorRadar
from src.competitors.models import CompetitorProduct
from src.clients.alibaba_scraper import DirectAlibabaClient
from src.clients.direct_scraper import DirectAliExpressClient

STOP_WORDS = {
    "hot", "selling", "factory", "wholesale", "cheap", "high", "quality",
    "new", "design", "custom", "logo", "2024", "2025", "2026", "2027",
    "oem", "odm", "free", "shipping", "supplier", "dropshipping",
    "manufacturer", "best", "sale", "top", "trending", "fashion", "luxury",
    "china", "pcs", "set", "pack", "promotional", "gift"
}

TRANSLATION_MAP = {
    "acrylic": "acrílico",
    "makeup": "maquiagem",
    "cosmetic": "cosméticos",
    "organizer": "organizador",
    "storage": "porta",
    "box": "caixa",
    "holder": "suporte",
    "watch": "relógio",
    "smart": "inteligente",
    "dispenser": "dispenser",
    "automatic": "automático",
    "soap": "sabonete",
    "bottle": "garrafa",
    "thermal": "térmica",
    "water": "água",
    "led": "led",
    "digital": "digital",
    "case": "estojo",
    "bag": "bolsa",
    "car": "carro",
    "mount": "suporte",
    "wireless": "sem fio",
    "charger": "carregador",
    "pet": "pet",
    "dog": "cachorro",
    "cat": "gato",
    "toy": "brinquedo",
    "kitchen": "cozinha",
    "tool": "ferramenta",
    "knife": "faca",
    "cutter": "cortador",
    "brush": "escova",
    "cleaning": "limpeza",
}

class ArbitrageEngine:
    """Discovers high-demand China wholesale products and crosses them with Mercado Livre Brasil."""

    def __init__(
        self,
        usd_rate: float = 5.50,
        icms_rate: float = 0.17,
        import_tax_rate: float = 0.60,
        marketplace_fee_rate: float = 0.16,
        freight_rate_pct: float = 0.15,
        competitor_radar: Optional[CompetitorRadar] = None,
        alibaba_client: Optional[DirectAlibabaClient] = None,
        aliexpress_client: Optional[DirectAliExpressClient] = None,
    ):
        self.usd_rate = usd_rate
        self.icms_rate = icms_rate
        self.import_tax_rate = import_tax_rate
        self.marketplace_fee_rate = marketplace_fee_rate
        self.freight_rate_pct = freight_rate_pct

        self.radar = competitor_radar or CompetitorRadar()
        self.alibaba = alibaba_client or DirectAlibabaClient(usd_rate=usd_rate)
        self.aliexpress = aliexpress_client or DirectAliExpressClient()

    def clean_query_for_ml(self, china_title: str, base_query: str) -> str:
        """Converts an English/noisy supplier title into an effective Portuguese search query for Mercado Livre."""
        if base_query and len(base_query.strip()) >= 4:
            # If the user already gave a specific Portuguese query, that's often the best anchor
            base = base_query.strip().lower()
            # Try to supplement with 1-2 distinct keywords from title if relevant
            words = re.findall(r"[a-zA-Záéíóúãõç]+", china_title.lower())
            additions = []
            for w in words:
                if w in TRANSLATION_MAP and TRANSLATION_MAP[w] not in base:
                    additions.append(TRANSLATION_MAP[w])
                elif len(w) >= 4 and w not in STOP_WORDS and w not in base:
                    if w in ("led", "usb", "rgb", "pro", "mini", "plus"):
                        additions.append(w)
            if additions:
                return f"{base} {additions[0]}"
            return base

        # Extract tokens and translate
        words = re.findall(r"[a-zA-Záéíóúãõç]+", china_title.lower())
        meaningful: List[str] = []
        for w in words:
            if w in STOP_WORDS or len(w) <= 2:
                continue
            translated = TRANSLATION_MAP.get(w, w)
            if translated not in meaningful:
                meaningful.append(translated)

        # Pick top 3-4 keywords
        if meaningful:
            return " ".join(meaningful[:4])
        return base_query or "produto importado"

    def calculate_landed_costs(self, fob_brl: float) -> tuple[float, float, float, float]:
        """Calculates international freight, II (60%) and ICMS (17% grossed up) per unit."""
        freight = round(fob_brl * self.freight_rate_pct, 2)
        customs_base = fob_brl + freight
        import_tax = round(customs_base * self.import_tax_rate, 2)

        # ICMS "por dentro": Base = (customs_base + II) / (1 - ICMS)
        icms_base = (customs_base + import_tax) / (1.0 - self.icms_rate)
        icms = round(icms_base * self.icms_rate, 2)

        landed_cost = round(customs_base + import_tax + icms, 2)
        return import_tax, icms, freight, landed_cost

    def classify_opportunity(
        self,
        competitors_count: int,
        full_share_pct: float,
        net_margin_pct: float,
        avg_rating: Optional[float]
    ) -> tuple[str, str, str]:
        """Classifies the opportunity into strategic action tiers."""
        # 1. Oceano Azul: zero competition or negligible competition without Full
        if competitors_count == 0 or (competitors_count <= 2 and full_share_pct == 0.0):
            return (
                "OCEANO_AZUL",
                "Oceano Azul (Pioneirismo)",
                "Produto campeão na China sem concorrência estabelecida no ML. Oportunidade de ditar preço e liderar o ranking!"
            )

        # 2. Alta Margem: healthy competition with massive spread
        if net_margin_pct >= 35.0:
            return (
                "ALTA_MARGEM",
                "Alta Margem (Arbitragem)",
                f"Spread excelente com {net_margin_pct:.1f}% de margem líquida real após taxas e impostos no Brasil."
            )

        # 3. Marca Própria: competitors exist but have weaknesses (low rating or no Full)
        if (avg_rating is not None and avg_rating < 4.3) or full_share_pct < 50.0 or net_margin_pct >= 22.0:
            weakness = "avaliações medianas" if (avg_rating and avg_rating < 4.3) else "poucos concorrentes no Full"
            return (
                "MARCA_PROPRIA",
                "Marca Própria (Diferenciação)",
                f"Mercado com espaço para marca própria ({weakness}). Entre com kit, embalagem premium e estoque no Full."
            )

        # 4. Saturado: margin squeezed or extreme price war in Full
        return (
            "SATURADO",
            "Saturado (Guerra de Preços)",
            f"Margem líquida comprimida ({net_margin_pct:.1f}%) e concorrência agressiva. Evite queimar capital."
        )

    def analyze_item(self, china_item: Dict[str, Any], base_query: str, source: str) -> ArbitrageItem:
        """Enriches a single China product by querying Mercado Livre competitors and calculating unit economics."""
        title = china_item.get("title", "")
        fob_brl = float(china_item.get("price", 0.0))
        fob_usd = round(fob_brl / self.usd_rate, 2) if self.usd_rate > 0 else 0.0
        moq = int(china_item.get("moq", 1))

        # Calculate taxes and landed unit cost
        import_tax, icms, freight, landed_cost = self.calculate_landed_costs(fob_brl)

        # Search Mercado Livre
        ml_query = self.clean_query_for_ml(title, base_query)
        competitors: List[CompetitorProduct] = []
        try:
            competitors = self.radar.find_competitors(ml_query, limit=5)
        except Exception:
            competitors = []

        prices = [c.price_brl for c in competitors if c.price_brl > 0]
        comp_count = len(competitors)

        if prices:
            min_p = round(min(prices), 2)
            max_p = round(max(prices), 2)
            avg_p = round(statistics.mean(prices), 2)
            full_count = sum(1 for c in competitors if c.shipping_type == "Full")
            full_share = round((full_count / comp_count) * 100, 1)

            ratings = [c.rating for c in competitors if c.rating is not None and c.rating > 0]
            avg_rating = round(statistics.mean(ratings), 1) if ratings else None

            top_comp_url = competitors[0].url
            top_comp_title = competitors[0].title

            # Sale reference price is the average market price in Brazil
            sale_price = avg_p
        else:
            min_p = max_p = avg_p = 0.0
            full_share = 0.0
            avg_rating = None
            top_comp_url = ""
            top_comp_title = ""

            # When no competitors exist, simulate 40% margin markup
            # sale_price = landed_cost / (1 - fee - margin)
            denom = max(0.1, 1.0 - self.marketplace_fee_rate - 0.40)
            sale_price = round(landed_cost / denom, 2)

        # Calculate Net Profit and Margin
        ml_fee = round(sale_price * self.marketplace_fee_rate, 2)
        net_profit = round(sale_price - ml_fee - landed_cost, 2)
        net_margin = round((net_profit / sale_price) * 100.0, 1) if sale_price > 0 else 0.0
        roi = round((net_profit / landed_cost) * 100.0, 1) if landed_cost > 0 else 0.0

        # Strategic classification
        strategy, strategy_label, summary = self.classify_opportunity(
            competitors_count=comp_count,
            full_share_pct=full_share,
            net_margin_pct=net_margin,
            avg_rating=avg_rating
        )

        return ArbitrageItem(
            source=source,
            china_id=str(china_item.get("id", "")),
            china_title=title,
            china_url=china_item.get("url", ""),
            china_fob_usd=fob_usd,
            china_fob_brl=fob_brl,
            moq=moq,
            supplier_name=china_item.get("supplier_name", "Fornecedor China"),
            is_verified=bool(china_item.get("is_verified", False)),
            has_trade_assurance=bool(china_item.get("has_trade_assurance", False)),
            china_sales=china_item.get("sales"),
            china_rating=china_item.get("rating"),
            import_tax_unit_brl=import_tax,
            icms_unit_brl=icms,
            freight_unit_brl=freight,
            landed_cost_unit_brl=landed_cost,
            ml_query=ml_query,
            ml_competitors_count=comp_count,
            ml_min_price=min_p,
            ml_avg_price=avg_p,
            ml_max_price=max_p,
            ml_full_share_pct=full_share,
            ml_top_competitor_url=top_comp_url,
            ml_top_competitor_title=top_comp_title,
            ml_avg_rating=avg_rating,
            reference_sale_price_brl=sale_price,
            ml_fee_brl=ml_fee,
            net_profit_brl=net_profit,
            net_margin_pct=net_margin,
            roi_pct=roi,
            strategy=strategy,
            strategy_label=strategy_label,
            summary=summary,
        )

    def scan(
        self,
        query: str,
        source: str = "alibaba",
        max_items: int = 15,
        max_moq: int = 500
    ) -> ArbitrageReport:
        """Executes full search and cross-referencing scan."""
        raw_items: List[Dict[str, Any]] = []

        if source.lower() in ("alibaba", "b2b"):
            raw_items = self.alibaba.search(query, max_items=max_items)
            source_label = "Alibaba"
            if not raw_items:
                fallback_items = self.aliexpress.search(query, max_items=max_items)
                if fallback_items:
                    raw_items = fallback_items
                    source_label = "AliExpress (Fallback)"
        elif source.lower() in ("ali", "aliexpress", "b2c"):
            raw_items = self.aliexpress.search(query, max_items=max_items)
            source_label = "AliExpress"
        else:
            # Hybrid scan: sample both
            ali_items = self.alibaba.search(query, max_items=max(5, max_items // 2))
            aex_items = self.aliexpress.search(query, max_items=max(5, max_items // 2))
            raw_items = ali_items + aex_items
            if not raw_items:
                raw_items = self.aliexpress.search(query, max_items=max_items)
            source_label = "Alibaba & AliExpress"

        # Filter by MOQ if applicable
        if max_moq and max_moq > 0:
            raw_items = [it for it in raw_items if int(it.get("moq", 1)) <= max_moq]

        analyzed_items: List[ArbitrageItem] = []
        for it in raw_items[:max_items]:
            item_source = "AliExpress" if "sales" in it else "Alibaba"
            analyzed = self.analyze_item(it, base_query=query, source=item_source)
            analyzed_items.append(analyzed)

        # Sort by best opportunities: Blue Ocean and High Margin first
        analyzed_items.sort(
            key=lambda x: (
                0 if x.strategy == "OCEANO_AZUL" else (1 if x.strategy == "ALTA_MARGEM" else (2 if x.strategy == "MARCA_PROPRIA" else 3)),
                -x.net_margin_pct
            )
        )

        blue_ocean = sum(1 for it in analyzed_items if it.strategy == "OCEANO_AZUL")
        high_margin = sum(1 for it in analyzed_items if it.strategy == "ALTA_MARGEM")
        private_label = sum(1 for it in analyzed_items if it.strategy == "MARCA_PROPRIA")
        saturated = sum(1 for it in analyzed_items if it.strategy == "SATURADO")

        return ArbitrageReport(
            query=query,
            source=source_label,
            usd_rate=self.usd_rate,
            total_scanned=len(analyzed_items),
            items=analyzed_items,
            blue_ocean_count=blue_ocean,
            high_margin_count=high_margin,
            private_label_count=private_label,
            saturated_count=saturated,
        )
