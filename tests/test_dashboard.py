from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from src.mercado_livre.dashboard_data import read_report, reports_in
from src.mercado_livre.dashboard_api import create_app


def test_read_report_real_file():
    report_path = Path("reports/Radar_Mercado_Livre_2026-09-16.xlsx")
    if not report_path.exists():
        pytest.skip("Relatório real não encontrado em reports/")
    data = read_report(report_path)
    assert data["id"] == "211833a8ae2b4a51a452c94440fb644d"
    assert len(data["products"]) == 100
    first = data["products"][0]
    assert first["id"] == "MLB69694728"
    assert first["demand"] == 100.0
    assert first["brand"] == 46.7
    assert first["combined"] == 68.3


def test_dashboard_api_auth_and_data(tmp_path):
    # Test unauthenticated access
    app = create_app(report_dir=str(tmp_path), access_key="test-key-at-least-24-characters-long", secure=False)
    client = TestClient(app)

    # Check initial session
    r = client.get("/radar/api/session")
    assert r.status_code == 200
    assert r.json() == {"authenticated": False}

    # Data endpoint without auth fails 401
    r = client.get("/radar/api/data")
    assert r.status_code == 401

    # Login with wrong key
    r = client.post("/radar/api/session", json={"key": "wrong-key"})
    assert r.status_code == 401

    # Login with right key
    r = client.post("/radar/api/session", json={"key": "test-key-at-least-24-characters-long"})
    assert r.status_code == 200
    assert r.json() == {"ok": True}

    # Session is now authenticated
    r = client.get("/radar/api/session")
    assert r.status_code == 200
    assert r.json() == {"authenticated": True}

    # Data endpoint works
    r = client.get("/radar/api/data")
    assert r.status_code == 200
    assert "runs" in r.json()
    assert r.json()["runs"] == []

    # Logout
    r = client.post("/radar/api/logout")
    assert r.status_code == 200

    # Data endpoint 401 again
    r = client.get("/radar/api/data")
    assert r.status_code == 401


def test_dashboard_import_and_download(tmp_path):
    report_path = Path("reports/Radar_Mercado_Livre_2026-09-16.xlsx")
    if not report_path.exists():
        pytest.skip("Relatório real não encontrado em reports/")

    app = create_app(report_dir=str(tmp_path), access_key="test-key-at-least-24-characters-long", secure=False)
    client = TestClient(app)

    # Authenticate
    r = client.post("/radar/api/session", json={"key": "test-key-at-least-24-characters-long"})
    assert r.status_code == 200

    # Import the report
    with report_path.open("rb") as f:
        r = client.post("/radar/api/import", content=f.read())
    assert r.status_code == 200
    res = r.json()
    assert res["duplicate"] is False
    assert res["id"] == "211833a8ae2b4a51a452c94440fb644d"

    # Re-importing detects duplicate
    with report_path.open("rb") as f:
        r = client.post("/radar/api/import", content=f.read())
    assert r.status_code == 200
    assert r.json()["duplicate"] is True

    # Check data
    r = client.get("/radar/api/data")
    assert r.status_code == 200
    runs = r.json()["runs"]
    assert len(runs) == 1
    assert runs[0]["id"] == "211833a8ae2b4a51a452c94440fb644d"

    # Download report
    r = client.get(f"/radar/api/reports/{res['id']}")
    assert r.status_code == 200
    assert len(r.content) > 0

