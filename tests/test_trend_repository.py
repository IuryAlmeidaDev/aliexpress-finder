# tests/test_trend_repository.py
import sqlite3
from datetime import datetime, timedelta, timezone

from src.trends.repository import TrendRepository


def _make_repo() -> TrendRepository:
    repo = TrendRepository(":memory:")
    repo.initialize()
    return repo


def test_initialize_creates_tables():
    repo = _make_repo()
    conn = repo._conn
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    assert "trend_terms" in tables
    assert "trend_snapshots" in tables
    assert "trend_opportunities" in tables


def test_seed_default_terms():
    repo = _make_repo()
    repo.seed_default_terms()
    terms = repo.get_active_terms()
    assert len(terms) >= 50
    assert all(t.active for t in terms)


def test_seed_default_terms_idempotent():
    repo = _make_repo()
    repo.seed_default_terms()
    count1 = len(repo.get_active_terms())
    repo.seed_default_terms()
    count2 = len(repo.get_active_terms())
    assert count1 == count2


def test_save_and_query_snapshots():
    repo = _make_repo()
    repo.seed_default_terms()
    terms = repo.get_active_terms()
    term = terms[0]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    snapshots = [
        {"term_id": term.id, "source": "aliexpress", "product_id": "p1",
         "title": "Test Product", "price_brl": 50.0, "price_usd": 10.0,
         "sales_total": 1000, "rating": 4.5, "moq": None,
         "supplier_name": None, "is_verified": None,
         "url": "https://example.com/p1", "collected_at": today}
    ]
    repo.save_snapshots(snapshots)
    history = repo.get_snapshots_for_velocity("p1", "aliexpress", days=7)
    assert len(history) == 1
    assert history[0][1] == 1000


def test_save_snapshots_ignores_duplicates():
    repo = _make_repo()
    repo.seed_default_terms()
    terms = repo.get_active_terms()
    term = terms[0]
    snap = {"term_id": term.id, "source": "aliexpress", "product_id": "p1",
            "title": "Test", "price_brl": 50.0, "price_usd": 10.0,
            "sales_total": 1000, "rating": 4.5, "moq": None,
            "supplier_name": None, "is_verified": None,
            "url": "https://example.com/p1", "collected_at": "2026-09-27"}
    repo.save_snapshots([snap])
    repo.save_snapshots([snap])  # duplicate
    history = repo.get_snapshots_for_velocity("p1", "aliexpress", days=30)
    assert len(history) == 1


def test_save_and_query_opportunities():
    repo = _make_repo()
    repo.seed_default_terms()
    terms = repo.get_active_terms()
    term = terms[0]
    snap = {"term_id": term.id, "source": "aliexpress", "product_id": "p1",
            "title": "Trending Item", "price_brl": 50.0, "price_usd": 10.0,
            "sales_total": 5000, "rating": 4.8, "moq": None,
            "supplier_name": None, "is_verified": None,
            "url": "https://example.com/p1", "collected_at": "2026-09-27"}
    repo.save_snapshots([snap])
    # Get snapshot_id
    row = repo._conn.execute("SELECT id FROM trend_snapshots LIMIT 1").fetchone()
    opp = {
        "snapshot_id": row[0], "product_id": "p1", "source": "aliexpress",
        "sales_velocity_7d": 3000, "sales_velocity_30d": 5000,
        "acceleration": 50.0, "ml_query": "item trending",
        "ml_competitors": 0, "ml_avg_price": 0.0, "ml_min_price": 0.0,
        "ml_full_share_pct": 0.0, "ml_total_sales_br": 0,
        "landed_cost_brl": 25.0, "suggested_price_brl": 89.90,
        "net_margin_pct": 54.0, "strategy": "OCEANO_AZUL",
        "trend_score": 92.0, "calculated_at": "2026-09-27T06:00:00Z"
    }
    repo.save_opportunities([opp])
    results = repo.get_trending(strategy="OCEANO_AZUL", category=None, limit=10)
    assert len(results) == 1
    assert results[0]["trend_score"] == 92.0


def test_get_trending_filters():
    repo = _make_repo()
    repo.seed_default_terms()
    terms = repo.get_active_terms()
    term = terms[0]
    snap = {"term_id": term.id, "source": "aliexpress", "product_id": "p1",
            "title": "Test", "price_brl": 50.0, "price_usd": 10.0,
            "sales_total": 5000, "rating": 4.8, "moq": None,
            "supplier_name": None, "is_verified": None,
            "url": "https://example.com/p1", "collected_at": "2026-09-27"}
    repo.save_snapshots([snap])
    row = repo._conn.execute("SELECT id FROM trend_snapshots LIMIT 1").fetchone()
    opp = {
        "snapshot_id": row[0], "product_id": "p1", "source": "aliexpress",
        "sales_velocity_7d": 3000, "sales_velocity_30d": 5000,
        "acceleration": 50.0, "ml_query": "test", "ml_competitors": 0,
        "ml_avg_price": 0.0, "ml_min_price": 0.0, "ml_full_share_pct": 0.0,
        "ml_total_sales_br": 0, "landed_cost_brl": 25.0,
        "suggested_price_brl": 89.90, "net_margin_pct": 54.0,
        "strategy": "OCEANO_AZUL", "trend_score": 92.0,
        "calculated_at": "2026-09-27T06:00:00Z"
    }
    repo.save_opportunities([opp])
    assert len(repo.get_trending(strategy="SATURADO", category=None, limit=10)) == 0
    assert len(repo.get_trending(strategy=None, category=None, limit=10)) == 1


def test_cleanup_old():
    repo = _make_repo()
    repo.seed_default_terms()
    terms = repo.get_active_terms()
    term = terms[0]
    old_date = (datetime.now(timezone.utc) - timedelta(days=100)).strftime("%Y-%m-%d")
    snap = {"term_id": term.id, "source": "aliexpress", "product_id": "old1",
            "title": "Old Product", "price_brl": 10.0, "price_usd": 2.0,
            "sales_total": 100, "rating": 3.0, "moq": None,
            "supplier_name": None, "is_verified": None,
            "url": "https://example.com/old1", "collected_at": old_date}
    repo.save_snapshots([snap])
    assert len(repo.get_snapshots_for_velocity("old1", "aliexpress", days=200)) == 1
    repo.cleanup_old(days=90)
    assert len(repo.get_snapshots_for_velocity("old1", "aliexpress", days=200)) == 0


def test_get_stats_empty():
    repo = _make_repo()
    stats = repo.get_stats()
    assert stats["total_monitored"] == 0
    assert stats["ocean_blue_count"] == 0


def test_get_sparkline():
    repo = _make_repo()
    repo.seed_default_terms()
    terms = repo.get_active_terms()
    term = terms[0]
    for i in range(5):
        d = (datetime.now(timezone.utc) - timedelta(days=4 - i)).strftime("%Y-%m-%d")
        snap = {"term_id": term.id, "source": "aliexpress", "product_id": "sp1",
                "title": "Sparkline Test", "price_brl": 50.0, "price_usd": 10.0,
                "sales_total": 100 * (i + 1), "rating": 4.0, "moq": None,
                "supplier_name": None, "is_verified": None,
                "url": "https://example.com/sp1", "collected_at": d}
        repo.save_snapshots([snap])
    sparkline = repo.get_sparkline("sp1", "aliexpress", points=30)
    assert sparkline == [100, 200, 300, 400, 500]
