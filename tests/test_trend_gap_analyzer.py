# tests/test_trend_gap_analyzer.py
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from src.trends.gap_analyzer import analyze_gaps, MAX_GAP_ANALYSIS
from src.trends.models import TrendVelocity, STRATEGY_OCEANO_AZUL, STRATEGY_PENDENTE
from src.trends.repository import TrendRepository


def _make_velocity(**overrides) -> TrendVelocity:
    defaults = dict(
        product_id="p1", source="aliexpress", title="Wireless Earbuds V2",
        url="https://aliexpress.com/item/p1.html", category="Eletrônicos",
        price_brl=50.0, sales_total=5000, sales_velocity_7d=3000,
        sales_velocity_30d=10000, acceleration=100.0,
    )
    defaults.update(overrides)
    return TrendVelocity(**defaults)


def _make_repo() -> TrendRepository:
    repo = TrendRepository(":memory:")
    repo.initialize()
    repo.seed_default_terms()
    terms = repo.get_active_terms()
    term = terms[0]
    repo.save_snapshots([{
        "term_id": term.id, "source": "aliexpress", "product_id": "p1",
        "title": "Wireless Earbuds V2", "price_brl": 50.0, "price_usd": 10.0,
        "sales_total": 5000, "rating": 4.8, "moq": None,
        "supplier_name": None, "is_verified": None,
        "url": "https://aliexpress.com/item/p1.html",
        "collected_at": datetime.now(timezone.utc).strftime("%Y-%m-%d")
    }])
    return repo


def test_max_gap_analysis_constant():
    assert MAX_GAP_ANALYSIS == 100


@patch("src.trends.gap_analyzer.get_usd_brl_rate")
@patch("src.trends.gap_analyzer.CompetitorRadar")
def test_analyze_gaps_oceano_azul(mock_radar_cls, mock_rate):
    mock_rate.return_value = MagicMock(rate=5.50)
    mock_radar = MagicMock()
    mock_radar.find_competitors.return_value = []  # 0 competitors → Oceano Azul
    mock_radar_cls.return_value = mock_radar

    repo = _make_repo()
    velocities = [_make_velocity(sales_velocity_7d=8000)]
    results = analyze_gaps(velocities, repo)
    assert len(results) == 1
    assert results[0].ml_competitors == 0
    assert results[0].strategy == STRATEGY_OCEANO_AZUL


@patch("src.trends.gap_analyzer.get_usd_brl_rate")
@patch("src.trends.gap_analyzer.CompetitorRadar")
def test_analyze_gaps_with_competitors(mock_radar_cls, mock_rate):
    mock_rate.return_value = MagicMock(rate=5.50)
    mock_radar = MagicMock()
    mock_competitor = MagicMock()
    mock_competitor.price_brl = 129.90
    mock_competitor.shipping_type = "Full"
    mock_radar.find_competitors.return_value = [mock_competitor] * 5
    mock_radar_cls.return_value = mock_radar

    repo = _make_repo()
    velocities = [_make_velocity(sales_velocity_7d=3000)]
    results = analyze_gaps(velocities, repo)
    assert len(results) == 1
    assert results[0].ml_competitors == 5


@patch("src.trends.gap_analyzer.get_usd_brl_rate")
@patch("src.trends.gap_analyzer.CompetitorRadar")
def test_analyze_gaps_ml_failure_marks_pendente(mock_radar_cls, mock_rate):
    mock_rate.return_value = MagicMock(rate=5.50)
    mock_radar = MagicMock()
    mock_radar.find_competitors.side_effect = Exception("ML blocked")
    mock_radar_cls.return_value = mock_radar

    repo = _make_repo()
    velocities = [_make_velocity(price_brl=50.0)]
    results = analyze_gaps(velocities, repo)
    assert len(results) == 1
    assert results[0].strategy == STRATEGY_PENDENTE
    assert results[0].ml_competitors is None
    assert results[0].landed_cost_brl is not None
    assert results[0].landed_cost_brl == 110.84
    assert results[0].suggested_price_brl is not None
    assert results[0].suggested_price_brl == 184.73
    assert results[0].net_margin_pct == 24.0


@patch("src.trends.gap_analyzer.get_usd_brl_rate")
@patch("src.trends.gap_analyzer.CompetitorRadar")
def test_analyze_gaps_respects_max_limit(mock_radar_cls, mock_rate):
    mock_rate.return_value = MagicMock(rate=5.50)
    mock_radar = MagicMock()
    mock_radar.find_competitors.return_value = []
    mock_radar_cls.return_value = mock_radar

    repo = _make_repo()
    # Save additional snapshots for 150 products
    terms = repo.get_active_terms()
    for i in range(150):
        repo.save_snapshots([{
            "term_id": terms[0].id, "source": "aliexpress",
            "product_id": f"px{i}", "title": f"Product {i}",
            "price_brl": 50.0, "price_usd": 10.0, "sales_total": 5000,
            "rating": 4.5, "moq": None, "supplier_name": None,
            "is_verified": None, "url": f"https://example.com/px{i}",
            "collected_at": datetime.now(timezone.utc).strftime("%Y-%m-%d")
        }])

    velocities = [_make_velocity(product_id=f"px{i}", sales_velocity_7d=5000 - i)
                  for i in range(150)]
    results = analyze_gaps(velocities, repo)
    assert len(results) <= MAX_GAP_ANALYSIS
