import pytest
from src.competitors.models import TargetProduct, CompetitorProduct
from src.competitors.benchmarking import BenchmarkingEngine

def test_benchmarking_price_metrics():
    target = TargetProduct(
        title="Óculos de Sol Quadrado",
        reference_price_brl=60.0,
        clean_query="oculos de sol quadrado"
    )
    competitors = [
        CompetitorProduct(title="C1", url="http://1", store_name="S1", platform="ML", price_brl=40.0, shipping_type="Full", kit_items=["estojo"]),
        CompetitorProduct(title="C2", url="http://2", store_name="S2", platform="ML", price_brl=60.0, shipping_type="Normal"),
        CompetitorProduct(title="C3", url="http://3", store_name="S3", platform="ML", price_brl=80.0, shipping_type="Full", kit_items=["estojo", "flanela"]),
    ]

    engine = BenchmarkingEngine(usd_rate=5.50, target_margin_pct=0.35, marketplace_fee_pct=0.16)
    dossier = engine.generate_dossier(target, competitors)

    assert dossier.min_competitor_price == 40.0
    assert dossier.max_competitor_price == 80.0
    assert dossier.avg_competitor_price == 60.0
    assert dossier.median_competitor_price == 60.0
    assert dossier.full_shipping_share_pct == round(2 / 3 * 100, 1)
    assert "estojo" in dossier.common_kit_items
    assert dossier.target_fob_china_usd > 0
    assert len(dossier.market_gaps) > 0

def test_benchmarking_empty_competitors():
    target = TargetProduct(
        title="Produto Raro",
        reference_price_brl=100.0,
        clean_query="produto raro"
    )
    engine = BenchmarkingEngine()
    dossier = engine.generate_dossier(target, [])

    assert dossier.min_competitor_price == 100.0
    assert dossier.max_competitor_price == 100.0
    assert dossier.avg_competitor_price == 100.0
    assert dossier.full_shipping_share_pct == 0.0
