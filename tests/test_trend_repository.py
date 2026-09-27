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
    indexes = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index'"
    ).fetchall()}
    assert "idx_snapshots_collected_at" in indexes
    assert "idx_snapshots_product" in indexes
    assert "idx_snapshots_term" in indexes
    assert "idx_opportunities_strategy" in indexes
    repo.close()


def test_seed_default_terms():
    repo = _make_repo()
    repo.seed_default_terms()
    terms = repo.get_active_terms()
    assert len(terms) >= 50
    assert all(t.active for t in terms)
    repo.close()


def test_seed_default_terms_idempotent():
    repo = _make_repo()
    repo.seed_default_terms()
    count1 = len(repo.get_active_terms())
    repo.seed_default_terms()
    count2 = len(repo.get_active_terms())
    assert count1 == count2
    repo.close()


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
    repo.close()


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
    repo.close()


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
    repo.close()


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
    repo.close()


def test_get_trending_by_category():
    repo = _make_repo()
    repo.seed_default_terms()
    terms = repo.get_active_terms()
    term_elec = next(t for t in terms if t.category == "Eletrônicos")
    term_casa = next(t for t in terms if t.category == "Casa & Cozinha")

    snap1 = {"term_id": term_elec.id, "source": "aliexpress", "product_id": "p_elec",
             "title": "Smart Watch", "price_brl": 100.0, "sales_total": 1000,
             "url": "http://x/e", "collected_at": "2026-09-27"}
    snap2 = {"term_id": term_casa.id, "source": "aliexpress", "product_id": "p_casa",
             "title": "Air Fryer", "price_brl": 200.0, "sales_total": 500,
             "url": "http://x/c", "collected_at": "2026-09-27"}
    repo.save_snapshots([snap1, snap2])

    row_elec = repo._conn.execute("SELECT id FROM trend_snapshots WHERE product_id='p_elec'").fetchone()
    row_casa = repo._conn.execute("SELECT id FROM trend_snapshots WHERE product_id='p_casa'").fetchone()

    opp1 = {
        "snapshot_id": row_elec[0], "product_id": "p_elec", "source": "aliexpress",
        "strategy": "OCEANO_AZUL", "trend_score": 85.0, "calculated_at": "2026-09-27T06:00:00Z"
    }
    opp2 = {
        "snapshot_id": row_casa[0], "product_id": "p_casa", "source": "aliexpress",
        "strategy": "TENDENCIA", "trend_score": 90.0, "calculated_at": "2026-09-27T06:00:00Z"
    }
    repo.save_opportunities([opp1, opp2])

    elec_results = repo.get_trending(category="Eletrônicos")
    assert len(elec_results) == 1
    assert elec_results[0]["product_id"] == "p_elec"
    assert elec_results[0]["category"] == "Eletrônicos"

    casa_results = repo.get_trending(category="Casa & Cozinha")
    assert len(casa_results) == 1
    assert casa_results[0]["product_id"] == "p_casa"
    assert casa_results[0]["category"] == "Casa & Cozinha"
    repo.close()


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
    repo.close()


def test_get_stats_empty():
    repo = _make_repo()
    stats = repo.get_stats()
    assert stats["total_monitored"] == 0
    assert stats["ocean_blue_count"] == 0
    repo.close()


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
    repo.close()


def test_get_all_product_ids_with_snapshots():
    repo = _make_repo()
    repo.seed_default_terms()
    terms = repo.get_active_terms()
    term = terms[0]

    d_old = (datetime.now(timezone.utc) - timedelta(days=5)).strftime("%Y-%m-%d")
    d_today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Product 1: spans 5 days with 2 snapshots -> qualifies
    snap1 = {"term_id": term.id, "source": "aliexpress", "product_id": "qual_1",
             "title": "Prod 1", "price_brl": 10.0, "sales_total": 100, "url": "http://x/1", "collected_at": d_old}
    snap2 = {"term_id": term.id, "source": "aliexpress", "product_id": "qual_1",
             "title": "Prod 1", "price_brl": 10.0, "sales_total": 150, "url": "http://x/1", "collected_at": d_today}

    # Product 2: only 1 snapshot -> does not meet COUNT >= 2
    snap3 = {"term_id": term.id, "source": "aliexpress", "product_id": "single_snap",
             "title": "Prod 2", "price_brl": 20.0, "sales_total": 50, "url": "http://x/2", "collected_at": d_old}

    repo.save_snapshots([snap1, snap2, snap3])
    prods = repo.get_all_product_ids_with_snapshots(min_days=2)
    assert len(prods) == 1
    assert prods[0] == ("qual_1", "aliexpress", term.category)
    repo.close()


def test_get_product_history():
    repo = _make_repo()
    repo.seed_default_terms()
    terms = repo.get_active_terms()
    term = terms[0]

    d1 = "2026-09-20"
    d2 = "2026-09-25"
    snapshots = [
        {"term_id": term.id, "source": "aliexpress", "product_id": "hist_1",
         "title": "Hist Item", "price_brl": 49.9, "sales_total": 100, "url": "http://x/h1", "collected_at": d1},
        {"term_id": term.id, "source": "aliexpress", "product_id": "hist_1",
         "title": "Hist Item", "price_brl": 45.0, "sales_total": 200, "url": "http://x/h1", "collected_at": d2},
    ]
    repo.save_snapshots(snapshots)
    history = repo.get_product_history("hist_1", "aliexpress")
    assert len(history) == 2
    assert history[0]["collected_at"] == d1
    assert history[0]["sales_total"] == 100
    assert history[0]["price_brl"] == 49.9
    assert history[1]["collected_at"] == d2
    assert history[1]["sales_total"] == 200
    assert history[1]["price_brl"] == 45.0
    repo.close()


def test_deactivate_stale_terms():
    repo = _make_repo()
    now = datetime.now(timezone.utc)
    old_created = (now - timedelta(days=40)).isoformat()
    new_created = now.isoformat()
    recent_snap_date = (now - timedelta(days=2)).strftime("%Y-%m-%d")

    repo._conn.execute(
        "INSERT INTO trend_terms (term, category, source, active, created_at) VALUES (?, ?, ?, 1, ?)",
        ("old_stale", "tech", "both", old_created)
    )
    repo._conn.execute(
        "INSERT INTO trend_terms (term, category, source, active, created_at) VALUES (?, ?, ?, 1, ?)",
        ("old_active", "tech", "both", old_created)
    )
    active_term_id = repo._conn.execute("SELECT id FROM trend_terms WHERE term='old_active'").fetchone()[0]

    repo._conn.execute(
        "INSERT INTO trend_terms (term, category, source, active, created_at) VALUES (?, ?, ?, 1, ?)",
        ("new_term", "tech", "both", new_created)
    )

    snap = {
        "term_id": active_term_id, "source": "aliexpress", "product_id": "p_act",
        "title": "Active Prod", "price_brl": 10.0, "sales_total": 50,
        "url": "http://x/a", "collected_at": recent_snap_date
    }
    repo.save_snapshots([snap])

    repo.deactivate_stale_terms(inactive_days=30)

    terms_by_term = {t.term: t.active for t in repo.get_active_terms()}
    assert "old_stale" not in terms_by_term
    assert terms_by_term.get("old_active") is True
    assert terms_by_term.get("new_term") is True
    repo.close()


def test_repo_init_creates_dir_and_close(tmp_path):
    db_file = tmp_path / "nested" / "sub" / "trends.db"
    repo = TrendRepository(str(db_file))
    repo.initialize()
    assert db_file.exists()
    repo.close()


def test_get_latest_snapshot():
    repo = _make_repo()
    repo.seed_default_terms()
    terms = repo.get_active_terms()
    term = terms[0]

    snap_old = {
        "term_id": term.id, "source": "aliexpress", "product_id": "p_latest",
        "title": "Old Title", "price_brl": 30.0, "price_usd": 6.0,
        "sales_total": 100, "rating": 4.0, "moq": 1,
        "supplier_name": "Supplier A", "is_verified": 0,
        "url": "https://example.com/p_old", "collected_at": "2026-09-20"
    }
    snap_new = {
        "term_id": term.id, "source": "aliexpress", "product_id": "p_latest",
        "title": "New Title", "price_brl": 45.0, "price_usd": 9.0,
        "sales_total": 250, "rating": 4.8, "moq": 2,
        "supplier_name": "Supplier B", "is_verified": 1,
        "url": "https://example.com/p_new", "collected_at": "2026-09-25"
    }
    repo.save_snapshots([snap_old, snap_new])

    latest = repo.get_latest_snapshot("p_latest", "aliexpress")
    assert latest is not None
    assert latest["title"] == "New Title"
    assert latest["price_brl"] == 45.0
    assert latest["sales_total"] == 250
    assert latest["rating"] == 4.8
    assert latest["moq"] == 2
    assert latest["supplier_name"] == "Supplier B"
    assert latest["is_verified"] == 1
    assert latest["url"] == "https://example.com/p_new"

    assert repo.get_latest_snapshot("nonexistent", "aliexpress") is None
    repo.close()


def test_get_latest_snapshot_id():
    repo = _make_repo()
    repo.seed_default_terms()
    terms = repo.get_active_terms()
    term = terms[0]

    snap_old = {
        "term_id": term.id, "source": "aliexpress", "product_id": "p_id",
        "title": "Item v1", "price_brl": 10.0, "price_usd": 2.0,
        "sales_total": 50, "rating": 4.0, "moq": None,
        "supplier_name": None, "is_verified": None,
        "url": "https://example.com/p1", "collected_at": "2026-09-20"
    }
    snap_new = {
        "term_id": term.id, "source": "aliexpress", "product_id": "p_id",
        "title": "Item v2", "price_brl": 12.0, "price_usd": 2.4,
        "sales_total": 80, "rating": 4.2, "moq": None,
        "supplier_name": None, "is_verified": None,
        "url": "https://example.com/p2", "collected_at": "2026-09-25"
    }
    repo.save_snapshots([snap_old, snap_new])

    latest_id = repo.get_latest_snapshot_id("p_id", "aliexpress")
    assert latest_id is not None

    expected_id = repo._conn.execute(
        "SELECT id FROM trend_snapshots WHERE product_id = 'p_id' AND source = 'aliexpress' "
        "ORDER BY collected_at DESC LIMIT 1"
    ).fetchone()["id"]
    assert latest_id == expected_id

    assert repo.get_latest_snapshot_id("nonexistent", "aliexpress") is None
    repo.close()

