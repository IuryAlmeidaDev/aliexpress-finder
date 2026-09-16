import statistics
from typing import List, Dict, Any
from src.competitors.models import TargetProduct, CompetitorProduct, MarketDossier

class BenchmarkingEngine:
    """Calculates market metrics, detects gaps, and estimates China sourcing target costs."""

    def __init__(
        self,
        usd_rate: float = 5.50,
        target_margin_pct: float = 0.35,
        marketplace_fee_pct: float = 0.16,
        icms_rate: float = 0.17,
        import_tax_rate: float = 0.60,
    ):
        self.usd_rate = usd_rate
        self.target_margin_pct = target_margin_pct
        self.marketplace_fee_pct = marketplace_fee_pct
        self.icms_rate = icms_rate
        self.import_tax_rate = import_tax_rate

    def generate_dossier(
        self,
        target: TargetProduct,
        competitors: List[CompetitorProduct],
        recommended_china_suppliers: List[Dict[str, Any]] = None
    ) -> MarketDossier:
        """Generates a complete MarketDossier from target and competitor list."""
        if not competitors:
            ref_price = target.reference_price_brl if target.reference_price_brl > 0 else 50.0
            target_fob_usd = self._calculate_target_fob(ref_price)
            return MarketDossier(
                target=target,
                competitors=[],
                min_competitor_price=ref_price,
                max_competitor_price=ref_price,
                avg_competitor_price=ref_price,
                median_competitor_price=ref_price,
                full_shipping_share_pct=0.0,
                common_kit_items=target.kit_items,
                market_gaps=["Nenhum concorrente direto encontrado para este termo exato. Oportunidade de pioneirismo!"],
                target_fob_china_usd=target_fob_usd,
                recommended_china_suppliers=recommended_china_suppliers or []
            )

        prices = [c.price_brl for c in competitors if c.price_brl > 0]
        if not prices:
            prices = [target.reference_price_brl]

        min_price = round(min(prices), 2)
        max_price = round(max(prices), 2)
        avg_price = round(statistics.mean(prices), 2)
        median_price = round(statistics.median(prices), 2)

        # Shipping share
        full_count = sum(1 for c in competitors if c.shipping_type == "Full")
        full_share = round((full_count / len(competitors)) * 100, 1)

        # Common kit items
        kit_counter: Dict[str, int] = {}
        for c in competitors:
            for item in c.kit_items:
                kit_counter[item] = kit_counter.get(item, 0) + 1
        common_kits = [k for k, count in sorted(kit_counter.items(), key=lambda x: x[1], reverse=True)]

        # Detect market gaps
        market_gaps = self._detect_market_gaps(competitors, full_share, common_kits, avg_price)

        # Sourcing target cost in China
        target_fob_usd = self._calculate_target_fob(avg_price)

        return MarketDossier(
            target=target,
            competitors=competitors,
            min_competitor_price=min_price,
            max_competitor_price=max_price,
            avg_competitor_price=avg_price,
            median_competitor_price=median_price,
            full_shipping_share_pct=full_share,
            common_kit_items=common_kits,
            market_gaps=market_gaps,
            target_fob_china_usd=target_fob_usd,
            recommended_china_suppliers=recommended_china_suppliers or []
        )

    def _calculate_target_fob(self, selling_price_brl: float) -> float:
        """Calculates maximum FOB China cost to achieve target net margin."""
        # Estimated deductions: marketplace fee + taxes (Simples ~6%) + desired margin
        deductions_pct = self.marketplace_fee_pct + 0.06 + self.target_margin_pct
        if deductions_pct >= 0.95:
            deductions_pct = 0.90
        
        max_landed_cost_brl = selling_price_brl * (1.0 - deductions_pct)
        if selling_price_brl < 79.0:
            # Fixed fee deduction for lower value items on marketplaces
            max_landed_cost_brl = max(5.0, max_landed_cost_brl - 6.0)

        # Reverse import taxes: Landed = (FOB * (1 + II)) / (1 - ICMS)
        # FOB = Landed * (1 - ICMS) / (1 + II)
        conversion_factor = (1.0 - self.icms_rate) / (1.0 + self.import_tax_rate)
        max_fob_brl = max_landed_cost_brl * conversion_factor
        max_fob_usd = max(0.20, max_fob_brl / self.usd_rate)

        return round(max_fob_usd, 2)

    def _detect_market_gaps(
        self,
        competitors: List[CompetitorProduct],
        full_share: float,
        common_kits: List[str],
        avg_price: float
    ) -> List[str]:
        """Identifies competitive openings and differentiation strategies."""
        gaps = []

        if full_share < 50.0:
            gaps.append("Poucos concorrentes utilizam Mercado Envios Full. Utilizar envio rápido garante vantagem imediata na Buy Box.")
        else:
            gaps.append("Mercado maduro em logística: concorrentes dominam o Full. Envio rápido é pré-requisito indispensável.")

        if not common_kits:
            gaps.append("Nenhum concorrente principal oferece kits ou brindes. Adicionar estojo, flanela ou embalagem premium criará grande diferenciação.")
        elif "estojo" not in common_kits and "case" not in common_kits:
            gaps.append("Concorrentes vendem sem estojo/case rígido. Criar oferta com case eleva o valor percebido sem encarecer o custo fabril.")
        else:
            gaps.append(f"O mercado espera kit com: {', '.join(common_kits[:3])}. Incluir esses acessórios de fábrica é essencial para manter paridade de oferta.")

        if avg_price > 100.0:
            gaps.append(f"Preço médio elevado (R$ {avg_price:.2f}). Há margem substancial para oferecer descontos promocionais agressivos ou kits mais completos.")

        return gaps
