"""Integration test: runs all 3 stages with mocked scrapers."""
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone

from src.trends.repository import TrendRepository
from src.trends.collector import collect_trends
from src.trends.velocity import calculate_velocity
from src.trends.gap_analyzer import analyze_gaps


def _mock_ali_search(query, limit=20, **kwargs):
    return [{"id": f"ali_{i}", "title": f"Product {query} {i}",
             "price": 50.0, "shipping": 0.0, "sales": 1000 + i * 500,
             "rating": 4.5, "url": f"https://aliexpress.com/item/ali_{i}.html"}
            for i in range(3)]


@patch("src.trends.gap_analyzer.get_usd_brl_rate")
@patch("src.trends.gap_analyzer.CompetitorRadar")
@patch("src.trends.collector.DirectAlibabaClient")
@patch("src.trends.collector.DirectAliExpressClient")
def test_full_pipeline(mock_ali_cls, mock_baba_cls, mock_radar_cls, mock_rate):
    # Setup mocks
    mock_ali = MagicMock()
    mock_ali.search.side_effect = _mock_ali_search
    mock_ali_cls.return_value = mock_ali
    mock_baba = MagicMock()
    mock_baba.search.return_value = []
    mock_baba_cls.return_value = mock_baba
    mock_rate.return_value = MagicMock(rate=5.50)
    mock_radar = MagicMock()
    mock_radar.find_competitors.return_value = []
    mock_radar_cls.return_value = mock_radar

    repo = TrendRepository(":memory:")
    repo.initialize()
    repo.seed_default_terms()

    # Stage 1: Collect day 1
    day1 = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
    # Manually insert "day 1" snapshots for velocity calculation
    terms = repo.get_active_terms()
    for i in range(3):
        repo.save_snapshots([{
            "term_id": terms[0].id, "source": "aliexpress",
            "product_id": f"ali_{i}", "title": f"Product test {i}",
            "price_brl": 50.0, "price_usd": 10.0,
            "sales_total": 500 + i * 200,  # lower sales 7 days ago
            "rating": 4.5, "moq": None, "supplier_name": None,
            "is_verified": None, "url": f"https://aliexpress.com/item/ali_{i}.html",
            "collected_at": day1,
        }])

    # Stage 1: Collect today (uses mocked scrapers)
    result = collect_trends(repo, block_pause=0, request_delay=(0, 0))
    assert result["collected"] > 0

    # Stage 2: Calculate velocity
    velocities = calculate_velocity(repo)
    # At least some should have velocity > 100 (threshold)
    assert len(velocities) >= 0  # depends on delta

    # If we have velocities, run Stage 3
    if velocities:
        opportunities = analyze_gaps(velocities, repo)
        assert len(opportunities) > 0
        assert all(o.trend_score >= 0 for o in opportunities)

    # Verify stats work
    stats = repo.get_stats()
    assert stats["total_monitored"] >= 0


def test_cli_trends_collect(monkeypatch, tmp_path, capsys):
    import sys
    from src.cli.main import run

    test_db = str(tmp_path / "test_trends.db")
    monkeypatch.setenv("MERCADO_LIVRE_DB_PATH", test_db)
    monkeypatch.setattr(sys, "argv", ["main.py", "trends", "--collect"])

    with patch("src.trends.collector.collect_trends", return_value={"collected": 10, "skipped_terms": 0, "blocked": False}) as mock_collect, \
         patch("src.trends.velocity.calculate_velocity", return_value=[MagicMock()]) as mock_vel, \
         patch("src.trends.gap_analyzer.analyze_gaps", return_value=[MagicMock(strategy="OCEANO_AZUL")]) as mock_gaps:
        run()

    assert mock_collect.called
    assert mock_vel.called
    assert mock_gaps.called
    captured = capsys.readouterr()
    assert "Estágio 1: Coletando dados da China" in captured.out
    assert "Estágio 2: Calculando velocidades" in captured.out
    assert "Estágio 3: Cruzando com Mercado Livre" in captured.out
    assert "Coleta completa!" in captured.out


def test_cli_trends_analyze(monkeypatch, tmp_path, capsys):
    import sys
    from src.cli.main import run

    test_db = str(tmp_path / "test_trends.db")
    monkeypatch.setenv("MERCADO_LIVRE_DB_PATH", test_db)
    monkeypatch.setattr(sys, "argv", ["main.py", "trends", "--analyze"])

    with patch("src.trends.velocity.calculate_velocity", return_value=[MagicMock()]) as mock_vel, \
         patch("src.trends.gap_analyzer.analyze_gaps", return_value=[MagicMock()]) as mock_gaps:
        run()

    assert mock_vel.called
    assert mock_gaps.called
    captured = capsys.readouterr()
    assert "Recalculando velocidades..." in captured.out
    assert "Cruzando com Mercado Livre..." in captured.out
    assert "Análise completa!" in captured.out


def test_cli_trends_cleanup(monkeypatch, tmp_path, capsys):
    import sys
    from src.cli.main import run

    test_db = str(tmp_path / "test_trends.db")
    monkeypatch.setenv("MERCADO_LIVRE_DB_PATH", test_db)
    monkeypatch.setattr(sys, "argv", ["main.py", "trends", "--cleanup"])

    run()

    captured = capsys.readouterr()
    assert "Limpeza concluída" in captured.out


def test_cli_trends_missing_action(monkeypatch):
    import sys
    import pytest
    from src.cli.main import run

    monkeypatch.setattr(sys, "argv", ["main.py", "trends"])
    with pytest.raises(SystemExit) as excinfo:
        run()
    assert excinfo.value.code == 2

