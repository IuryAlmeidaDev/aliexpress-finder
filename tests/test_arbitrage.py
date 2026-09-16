import pytest
from pathlib import Path
from src.arbitrage.models import ArbitrageItem, ArbitrageReport
from src.arbitrage.engine import ArbitrageEngine
from src.arbitrage.exporter import export_arbitrage_excel
from src.competitors.models import CompetitorProduct

class MockRadar:
    def __init__(self, competitors=None):
        self.competitors = competitors or []

    def find_competitors(self, query: str, limit: int = 5):
        return self.competitors

class MockAlibaba:
    def __init__(self, items=None):
        self.items = items or []

    def search(self, query: str, max_items: int = 30):
        return self.items

class MockAliExpress:
    def __init__(self, items=None):
        self.items = items or []

    def search(self, query: str, max_items: int = 30):
        return self.items

def test_arbitrage_landed_cost_calculation():
    engine = ArbitrageEngine(usd_rate=5.50, icms_rate=0.17, import_tax_rate=0.60, freight_rate_pct=0.15)
    # FOB = R$ 10.00
    # Freight 15% = R$ 1.50 => Customs base = R$ 11.50
    # II 60% = 11.50 * 0.60 = R$ 6.90
    # Base ICMS = (11.50 + 6.90) / (1 - 0.17) = 18.40 / 0.83 = 22.1687
    # ICMS = 22.1687 * 0.17 = 3.77
    # Landed = 11.50 + 6.90 + 3.77 = 22.17
    import_tax, icms, freight, landed = engine.calculate_landed_costs(10.0)
    assert freight == 1.50
    assert import_tax == 6.90
    assert round(icms, 2) == 3.77
    assert round(landed, 2) == 22.17

def test_arbitrage_blue_ocean_classification():
    # 0 competitors on ML => OCEANO_AZUL
    radar = MockRadar(competitors=[])
    engine = ArbitrageEngine(usd_rate=5.50, competitor_radar=radar)

    item = {
        "id": "123456",
        "title": "Acrylic Makeup Organizer Case Box",
        "price": 10.0,
        "moq": 50,
        "supplier_name": "Yiwu Factory",
        "is_verified": True,
        "has_trade_assurance": True,
        "url": "https://alibaba.com/product/123456.html",
    }
    result = engine.analyze_item(item, base_query="organizador acrilico", source="Alibaba")
    assert result.strategy == "OCEANO_AZUL"
    assert result.ml_competitors_count == 0
    assert "Pioneirismo" in result.strategy_label

def test_arbitrage_high_margin_classification():
    # Competitors on ML selling at R$ 89.90 with high spread => ALTA_MARGEM
    comp = CompetitorProduct(
        title="Organizador de Maquiagem em Acrílico Giratório",
        url="https://mercadolivre.com.br/MLB999",
        store_name="Loja Beleza",
        platform="Mercado Livre",
        price_brl=89.90,
        shipping_type="Full",
        rating=4.8
    )
    radar = MockRadar(competitors=[comp])
    engine = ArbitrageEngine(usd_rate=5.50, competitor_radar=radar)

    item = {
        "id": "123456",
        "title": "Acrylic Makeup Organizer Case Box",
        "price": 12.0,  # FOB R$ 12 => Landed ~R$ 26.60 => Fee (16% of 89.90) = 14.38 => Profit ~48.92 => Margin > 50%
        "moq": 50,
        "supplier_name": "Yiwu Factory",
        "is_verified": True,
        "has_trade_assurance": True,
        "url": "https://alibaba.com/product/123456.html",
    }
    result = engine.analyze_item(item, base_query="organizador acrilico", source="Alibaba")
    assert result.strategy == "ALTA_MARGEM"
    assert result.net_margin_pct >= 35.0
    assert result.ml_competitors_count == 1

def test_arbitrage_scan_and_export(tmp_path):
    ali_items = [
        {"id": "1", "title": "Organizer 1", "price": 10.0, "moq": 50, "supplier_name": "Factory A", "url": "https://a.com"},
        {"id": "2", "title": "Organizer 2", "price": 15.0, "moq": 100, "supplier_name": "Factory B", "url": "https://b.com"}
    ]
    radar = MockRadar(competitors=[])
    ali_mock = MockAlibaba(items=ali_items)
    engine = ArbitrageEngine(competitor_radar=radar, alibaba_client=ali_mock)

    report = engine.scan(query="organizador acrilico", source="alibaba", max_items=2)
    assert report.total_scanned == 2
    assert report.blue_ocean_count == 2
    assert len(report.items) == 2

    # Test Excel Export
    excel_path = tmp_path / "test_arbitragem.xlsx"
    out = export_arbitrage_excel(report, output_path=excel_path)
    assert out.exists()
    assert out.stat().st_size > 1000

def test_arbitrage_fallback_when_alibaba_empty():
    ali_mock = MockAlibaba(items=[])
    aex_items = [
        {"id": "a1", "title": "Aex Product", "price": 20.0, "moq": 1, "sales": 1500, "rating": 4.9, "url": "https://aliexpress.com/item/a1"}
    ]
    aex_mock = MockAliExpress(items=aex_items)
    radar = MockRadar(competitors=[])
    engine = ArbitrageEngine(competitor_radar=radar, alibaba_client=ali_mock, aliexpress_client=aex_mock)

    report = engine.scan(query="produto teste", source="alibaba", max_items=5)
    assert report.total_scanned == 1
    assert "Fallback" in report.source
    assert report.items[0].china_title == "Aex Product"

