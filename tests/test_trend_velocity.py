# tests/test_trend_velocity.py
from datetime import datetime, timedelta, timezone

from src.trends.velocity import calculate_velocity, MIN_TREND_VELOCITY
from src.trends.repository import TrendRepository


def _make_repo_with_data(days_data: list[tuple[int, int]],
                          product_id: str = "p1") -> TrendRepository:
    """Create repo with snapshots. days_data = [(days_ago, sales_total), ...]"""
    repo = TrendRepository(":memory:")
    repo.initialize()
    repo.seed_default_terms()
    terms = repo.get_active_terms()
    term = terms[0]
    for days_ago, sales in days_data:
        d = (datetime.now(timezone.utc) - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        repo.save_snapshots([{
            "term_id": term.id, "source": "aliexpress", "product_id": product_id,
            "title": "Test Product", "price_brl": 50.0, "price_usd": 10.0,
            "sales_total": sales, "rating": 4.5, "moq": None,
            "supplier_name": None, "is_verified": None,
            "url": f"https://example.com/{product_id}", "collected_at": d
        }])
    return repo


def test_min_trend_velocity_constant():
    assert MIN_TREND_VELOCITY == 100


def test_velocity_7d_calculation():
    # 7 days ago: 1000 sales, today: 1800 sales → velocity_7d = 800
    repo = _make_repo_with_data([(7, 1000), (0, 1800)])
    results = calculate_velocity(repo)
    assert len(results) == 1
    assert results[0].sales_velocity_7d == 800


def test_velocity_30d_calculation():
    # 30 days ago: 500, 7 days ago: 1500, today: 2000
    repo = _make_repo_with_data([(30, 500), (7, 1500), (0, 2000)])
    results = calculate_velocity(repo)
    assert len(results) == 1
    assert results[0].sales_velocity_7d == 500
    assert results[0].sales_velocity_30d == 1500


def test_acceleration_calculation():
    # Week before last: velocity was 300 (1000→1300 in 7d)
    # Last week: velocity is 800 (1300→2100 in 7d)
    # Acceleration = (800 - 300) / 300 * 100 = 166.67%
    repo = _make_repo_with_data([(14, 1000), (7, 1300), (0, 2100)])
    results = calculate_velocity(repo)
    assert len(results) == 1
    assert results[0].sales_velocity_7d == 800
    assert round(results[0].acceleration, 1) == 166.7


def test_filters_below_threshold():
    # velocity_7d = 50, below MIN_TREND_VELOCITY of 100
    repo = _make_repo_with_data([(7, 1000), (0, 1050)])
    results = calculate_velocity(repo)
    assert len(results) == 0


def test_handles_single_snapshot():
    repo = _make_repo_with_data([(0, 5000)])
    results = calculate_velocity(repo)
    assert len(results) == 0  # needs ≥2 snapshots


def test_handles_null_sales():
    repo = TrendRepository(":memory:")
    repo.initialize()
    repo.seed_default_terms()
    terms = repo.get_active_terms()
    term = terms[0]
    repo.save_snapshots([{
        "term_id": term.id, "source": "aliexpress", "product_id": "pnull",
        "title": "Null Sales", "price_brl": 50.0, "price_usd": 10.0,
        "sales_total": None, "rating": 4.5, "moq": None,
        "supplier_name": None, "is_verified": None,
        "url": "https://example.com/pnull", "collected_at": "2026-09-27"
    }])
    results = calculate_velocity(repo)
    assert len(results) == 0


def test_handles_decreasing_sales():
    # Sales went down (possible data glitch) → velocity negative → filtered out
    repo = _make_repo_with_data([(7, 5000), (0, 4000)])
    results = calculate_velocity(repo)
    assert len(results) == 0  # negative velocity filtered


def test_sorted_by_velocity_descending():
    repo = TrendRepository(":memory:")
    repo.initialize()
    repo.seed_default_terms()
    terms = repo.get_active_terms()
    term = terms[0]
    for pid, v7, v0 in [("slow", 1000, 1200), ("fast", 1000, 5000), ("mid", 1000, 2000)]:
        for days_ago, sales in [(7, v7), (0, v0)]:
            d = (datetime.now(timezone.utc) - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            repo.save_snapshots([{
                "term_id": term.id, "source": "aliexpress", "product_id": pid,
                "title": f"Product {pid}", "price_brl": 50.0, "price_usd": 10.0,
                "sales_total": sales, "rating": 4.5, "moq": None,
                "supplier_name": None, "is_verified": None,
                "url": f"https://example.com/{pid}", "collected_at": d
            }])
    results = calculate_velocity(repo)
    assert results[0].product_id == "fast"
    assert results[1].product_id == "mid"
    assert results[2].product_id == "slow"
