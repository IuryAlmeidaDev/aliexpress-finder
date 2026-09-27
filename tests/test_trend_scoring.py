from src.trends.scoring import calculate_trend_score
from src.trends.models import (
    TrendVelocity, STRATEGY_OCEANO_AZUL, STRATEGY_TENDENCIA,
    STRATEGY_EMERGENTE, STRATEGY_SATURADO, STRATEGY_PENDENTE,
)


def _make_velocity(**overrides) -> TrendVelocity:
    defaults = dict(
        product_id="p1", source="aliexpress", title="Test", url="https://x.com",
        category="Eletrônicos", price_brl=50.0, sales_total=5000,
        sales_velocity_7d=5000, sales_velocity_30d=15000, acceleration=100.0,
    )
    defaults.update(overrides)
    return TrendVelocity(**defaults)


def test_oceano_azul_high_score():
    v = _make_velocity(sales_velocity_7d=8000)
    score, strategy = calculate_trend_score(v, ml_competitors=0,
                                            net_margin_pct=55.0,
                                            max_velocity_in_category=10000)
    assert score >= 75
    assert strategy == STRATEGY_OCEANO_AZUL


def test_tendencia_medium_score():
    v = _make_velocity(sales_velocity_7d=5000)
    score, strategy = calculate_trend_score(v, ml_competitors=5,
                                            net_margin_pct=40.0,
                                            max_velocity_in_category=10000)
    assert 50 <= score < 75
    assert strategy == STRATEGY_TENDENCIA


def test_emergente_lower_score():
    v = _make_velocity(sales_velocity_7d=3000)
    score, strategy = calculate_trend_score(v, ml_competitors=20,
                                            net_margin_pct=25.0,
                                            max_velocity_in_category=10000)
    assert 25 <= score < 50
    assert strategy == STRATEGY_EMERGENTE


def test_saturado_low_score():
    v = _make_velocity(sales_velocity_7d=500)
    score, strategy = calculate_trend_score(v, ml_competitors=80,
                                            net_margin_pct=5.0,
                                            max_velocity_in_category=10000)
    assert score < 25
    assert strategy == STRATEGY_SATURADO


def test_pendente_when_ml_data_missing():
    v = _make_velocity(sales_velocity_7d=5000)
    score, strategy = calculate_trend_score(v, ml_competitors=None,
                                            net_margin_pct=None,
                                            max_velocity_in_category=10000)
    assert strategy == STRATEGY_PENDENTE


def test_score_clamped_0_to_100():
    v = _make_velocity(sales_velocity_7d=100000)
    score, _ = calculate_trend_score(v, ml_competitors=0,
                                     net_margin_pct=99.0,
                                     max_velocity_in_category=1000)
    assert 0 <= score <= 100


def test_zero_max_velocity_no_crash():
    v = _make_velocity(sales_velocity_7d=500)
    score, _ = calculate_trend_score(v, ml_competitors=0,
                                     net_margin_pct=50.0,
                                     max_velocity_in_category=0)
    assert 0 <= score <= 100
