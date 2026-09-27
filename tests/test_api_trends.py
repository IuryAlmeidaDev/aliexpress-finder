import json
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.mercado_livre.dashboard_api import create_app
from src.trends.repository import TrendRepository


@pytest.fixture
def client(tmp_path):
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    db_path = str(tmp_path / "test.db")

    # Initialize trend tables
    repo = TrendRepository(db_path)
    repo.initialize()
    repo.seed_default_terms()

    # Insert test data
    terms = repo.get_active_terms()
    term = terms[0]
    repo.save_snapshots([{
        "term_id": term.id, "source": "aliexpress", "product_id": "test1",
        "title": "Trending Product", "price_brl": 50.0, "price_usd": 10.0,
        "sales_total": 5000, "rating": 4.8, "moq": None,
        "supplier_name": None, "is_verified": None,
        "url": "https://aliexpress.com/item/test1.html",
        "collected_at": datetime.now(timezone.utc).strftime("%Y-%m-%d")
    }])
    row = repo._conn.execute("SELECT id FROM trend_snapshots LIMIT 1").fetchone()
    repo.save_opportunities([{
        "snapshot_id": row["id"], "product_id": "test1", "source": "aliexpress",
        "sales_velocity_7d": 3000, "sales_velocity_30d": 10000,
        "acceleration": 50.0, "ml_query": "produto trending",
        "ml_competitors": 0, "ml_avg_price": 0.0, "ml_min_price": 0.0,
        "ml_full_share_pct": 0.0, "ml_total_sales_br": 0,
        "landed_cost_brl": 25.0, "suggested_price_brl": 89.90,
        "net_margin_pct": 54.0, "strategy": "OCEANO_AZUL",
        "trend_score": 92.0, "calculated_at": datetime.now(timezone.utc).isoformat()
    }])
    repo._conn.close()

    with patch.dict("os.environ", {"MERCADO_LIVRE_DB_PATH": db_path}):
        app = create_app(
            report_dir=str(report_dir),
            access_key="test-key-minimum-24-characters-long",
        )
        tc = TestClient(app)
        # Authenticate
        tc.post("/radar/api/session",
                json={"key": "test-key-minimum-24-characters-long"})
        yield tc


def test_get_trends(client):
    resp = client.get("/radar/api/trends")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert len(data["items"]) >= 1
    assert data["items"][0]["strategy"] == "OCEANO_AZUL"


def test_get_trends_filter_strategy(client):
    resp = client.get("/radar/api/trends?strategy=SATURADO")
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 0


def test_get_trends_stats(client):
    resp = client.get("/radar/api/trends/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_monitored" in data
    assert "ocean_blue_count" in data
    assert data["ocean_blue_count"] >= 1


def test_get_product_history(client):
    resp = client.get("/radar/api/trends/test1/history?source=aliexpress")
    assert resp.status_code == 200
    data = resp.json()
    assert "history" in data
    assert len(data["history"]) >= 1


def test_get_trends_terms(client):
    resp = client.get("/radar/api/trends/terms")
    assert resp.status_code == 200
    data = resp.json()
    assert "terms" in data
    assert len(data["terms"]) >= 50


def test_trends_requires_auth():
    from src.mercado_livre.dashboard_api import create_app
    app = create_app(access_key="test-key-minimum-24-characters-long")
    tc = TestClient(app)
    resp = tc.get("/radar/api/trends")
    assert resp.status_code == 401
