import os
import pandas as pd
from src.cli.exporter import export_to_excel
from src.cli.formatters import render_results_table

def test_export_to_excel(tmp_path):
    out_file = str(tmp_path / "test_opportunities.xlsx")
    records = [
        {
            "Produto": "Pagani Design Sapphire",
            "Preço Ali (R$)": 190.0,
            "Impostos BR (R$)": 85.0,
            "Custo Final (R$)": 275.0,
            "Sugestão Venda (R$)": 450.0,
            "Lucro Líquido (R$)": 103.0,
            "ROI (%)": 37.45,
            "Avaliação": 4.8,
            "Link": "https://aliexpress.com/item/1.html"
        }
    ]
    path = export_to_excel(records, out_file)
    assert os.path.exists(path)
    df = pd.read_excel(path)
    assert len(df) == 1
    assert df.iloc[0]["Produto"] == "Pagani Design Sapphire"

def test_render_results_table_runs_cleanly(capsys):
    records = [
        {
            "Produto": "Tandorio Automatic Sapphire",
            "Preço Ali (R$)": 210.0,
            "Impostos BR (R$)": 94.0,
            "Custo Final (R$)": 304.0,
            "Sugestão Venda (R$)": 499.0,
            "Lucro Líquido (R$)": 115.0,
            "ROI (%)": 37.8,
            "Avaliação": 4.9,
            "Link": "https://aliexpress.com/item/2.html"
        }
    ]
    render_results_table(records)


def test_cli_run_no_items(monkeypatch):
    import sys
    from unittest.mock import patch
    from src.cli.main import run

    monkeypatch.setattr(sys, "argv", ["main.py", "--busca", "relogio"])
    with patch("src.cli.main.DirectAliExpressClient.search", return_value=[]):
        try:
            run()
        except SystemExit as e:
            assert e.code == 0


def test_cli_run_success_with_export(monkeypatch, tmp_path):
    import sys
    from unittest.mock import patch
    from src.cli.main import run

    export_path = str(tmp_path / "cli_test_out.xlsx")
    mock_items = [
        {
            "title": "Relogio Automatico Pagani",
            "price": 200.0,
            "shipping": 0.0,
            "sales": 150,
            "rating": 4.8,
            "url": "https://aliexpress.com/item/1.html"
        }
    ]

    monkeypatch.setattr(sys, "argv", ["main.py", "--busca", "relogio", "--exportar"])
    with patch("src.cli.main.DirectAliExpressClient.search", return_value=mock_items), \
         patch("src.cli.main.export_to_excel", return_value=export_path) as mock_export:
        run()
        assert mock_export.called


def test_cli_run_all_filtered_out(monkeypatch):
    import sys
    from unittest.mock import patch
    from src.cli.main import run

    mock_items = [
        {
            "title": "Relogio Automatico Pagani",
            "price": 200.0,
            "shipping": 0.0,
            "sales": 150,
            "rating": 4.8,
            "url": "https://aliexpress.com/item/1.html"
        }
    ]

    monkeypatch.setattr(sys, "argv", ["main.py", "--busca", "relogio", "--max-custo", "50.0"])
    with patch("src.cli.main.DirectAliExpressClient.search", return_value=mock_items):
        try:
            run()
        except SystemExit as e:
            assert e.code == 0


def test_cli_help(monkeypatch, capsys):
    import sys
    from src.cli.main import run

    monkeypatch.setattr(sys, "argv", ["main.py", "--help"])
    try:
        run()
    except SystemExit as e:
        assert e.code == 0
    captured = capsys.readouterr()
    assert "AliExpress Resale Opportunity Finder" in captured.out


def test_cli_run_impossible_margin(monkeypatch, capsys):
    import sys
    from src.cli.main import run

    # 85% margin + default 16% marketplace fee = 101% >= 100%
    monkeypatch.setattr(sys, "argv", ["main.py", "--busca", "relogio", "--margem", "85.0"])
    try:
        run()
    except SystemExit as e:
        assert e.code == 1
    else:
        assert False, "CLI should have exited with SystemExit"

    captured = capsys.readouterr()
    assert "Erro:" in captured.out
    assert "menor que 100%" in captured.out


def test_cli_run_custom_min_sales_and_rating(monkeypatch):
    import sys
    from unittest.mock import patch
    from src.cli.main import run

    mock_items = [
        {
            "title": "Relogio Automatico Pagani Novo",
            "price": 80.0,
            "shipping": 0.0,
            "sales": 2,
            "rating": 3.8,
            "url": "https://aliexpress.com/item/1.html"
        }
    ]

    # With min-vendas 1 and min-nota 3.5, the item should be kept and rendered
    monkeypatch.setattr(sys, "argv", [
        "main.py", "--busca", "relogio", "--min-vendas", "1", "--min-nota", "3.5"
    ])
    with patch("src.cli.main.DirectAliExpressClient.search", return_value=mock_items), \
         patch("src.cli.main.render_results_table") as mock_render:
        run()
        assert mock_render.called
        assert len(mock_render.call_args[0][0]) == 1


def test_cli_run_choice_mode(monkeypatch):
    import sys
    from unittest.mock import patch
    from src.cli.main import run

    mock_items = [
        {
            "title": "Relogio Quartzo Choice",
            "price": 135.13,
            "shipping": 0.0,
            "sales": 150,
            "rating": 4.8,
            "url": "https://aliexpress.com/item/1.html"
        }
    ]

    monkeypatch.setattr(sys, "argv", ["main.py", "--busca", "relogio", "--choice"])
    with patch("src.cli.main.DirectAliExpressClient.search", return_value=mock_items), \
         patch("src.cli.main.render_results_table") as mock_render:
        run()
        assert mock_render.called
        records = mock_render.call_args[0][0]
        assert len(records) == 1
        assert abs(records[0]["Impostos BR (R$)"] - 27.69) <= 0.02
        assert abs(records[0]["Custo Final (R$)"] - 162.82) <= 0.02


def test_cli_mercado_livre_does_not_require_search_term(monkeypatch, tmp_path):
    import sys
    from unittest.mock import patch
    from src.cli.main import run
    from src.mercado_livre.service import RadarRunResult

    monkeypatch.setattr(sys, "argv", [
        "main.py", "--fonte", "mercado-livre", "--ml-db", str(tmp_path / "radar.db")
    ])
    result = RadarRunResult("run1", "success", "report.xlsx", 3, 1, [])
    with patch("src.cli.main.MercadoLivreRadar.run", return_value=result) as mock_run:
        run()
    assert mock_run.called


def test_cli_ali_with_manual_usd(monkeypatch):
    import sys
    from unittest.mock import patch
    from src.cli.main import run

    mock_items = [
        {
            "title": "Produto Teste USD",
            "price": 200.0,
            "shipping": 0.0,
            "sales": 50,
            "rating": 4.8,
            "url": "https://aliexpress.com/item/1.html"
        }
    ]

    monkeypatch.setattr(sys, "argv", ["main.py", "--busca", "teste", "--usd", "6.00"])
    with patch("src.cli.main.DirectAliExpressClient.search", return_value=mock_items), \
         patch("src.cli.main.render_results_table") as mock_render:
        run()
        assert mock_render.called



