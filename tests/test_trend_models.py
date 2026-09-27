from dataclasses import asdict
from src.trends.models import (
    TrendTerm, TrendSnapshot, TrendVelocity, TrendOpportunity,
    STRATEGY_OCEANO_AZUL, STRATEGY_TENDENCIA, STRATEGY_EMERGENTE,
    STRATEGY_SATURADO, STRATEGY_PENDENTE,
)


def test_trend_term_creation():
    t = TrendTerm(id=1, term="wireless earbuds", category="Eletrônicos",
                  source="both", active=True, created_at="2026-09-27T04:00:00Z",
                  last_hit_at=None)
    assert t.term == "wireless earbuds"
    assert t.active is True
    assert t.last_hit_at is None


def test_trend_snapshot_creation():
    s = TrendSnapshot(id=1, term_id=1, source="aliexpress", product_id="12345",
                      title="Wireless Earbuds V2", price_brl=89.90, price_usd=16.50,
                      sales_total=3400, rating=4.8, moq=None, supplier_name=None,
                      is_verified=None, url="https://aliexpress.com/item/12345.html",
                      collected_at="2026-09-27")
    assert s.product_id == "12345"
    assert s.moq is None


def test_trend_velocity_creation():
    v = TrendVelocity(product_id="12345", source="aliexpress",
                      title="Wireless Earbuds V2", url="https://example.com",
                      category="Eletrônicos", price_brl=89.90, sales_total=3400,
                      sales_velocity_7d=800, sales_velocity_30d=3000,
                      acceleration=25.0, rating=4.8, moq=None,
                      supplier_name=None, is_verified=None)
    assert v.sales_velocity_7d == 800
    assert v.acceleration == 25.0


def test_trend_opportunity_serialization():
    opp = TrendOpportunity(
        product_id="12345", source="aliexpress", title="Test",
        url="https://example.com", category="Eletrônicos", price_brl=89.90,
        sales_total=3400, sales_velocity_7d=800, sales_velocity_30d=3000,
        acceleration=25.0, ml_query="fone sem fio", ml_competitors=0,
        ml_avg_price=0.0, ml_min_price=0.0, ml_full_share_pct=0.0,
        ml_total_sales_br=0, landed_cost_brl=45.0, suggested_price_brl=129.90,
        net_margin_pct=54.0, strategy=STRATEGY_OCEANO_AZUL, trend_score=92.0,
        supplier_name=None, moq=None, is_verified=None,
        sparkline=[100, 200, 500, 1200, 3400], calculated_at="2026-09-27T06:00:00Z"
    )
    d = asdict(opp)
    assert d["strategy"] == "OCEANO_AZUL"
    assert d["sparkline"] == [100, 200, 500, 1200, 3400]
    assert isinstance(d, dict)


def test_strategy_constants():
    assert STRATEGY_OCEANO_AZUL == "OCEANO_AZUL"
    assert STRATEGY_TENDENCIA == "TENDENCIA"
    assert STRATEGY_EMERGENTE == "EMERGENTE"
    assert STRATEGY_SATURADO == "SATURADO"
    assert STRATEGY_PENDENTE == "PENDENTE"
