import os
import sys
import pandas as pd
from unittest.mock import patch
from src.cli.main import run
from src.cli.formatters import render_alibaba_table
from src.cli.exporter import export_to_excel

MOCK_ALIBABA_ITEMS = [
    {
        "id": "1",
        "title": "Kids Watch Silicone LED",
        "price": 6.00,
        "moq": 50,
        "supplier_name": "Shenzhen Factory Ltd",
        "is_verified": True,
        "has_trade_assurance": True,
        "years_in_business": 4,
        "url": "https://alibaba.com/product/1.html"
    }
]

def test_cli_alibaba_run_success_with_export(monkeypatch, tmp_path):
    export_file = str(tmp_path / "oportunidades_alibaba.xlsx")
    monkeypatch.setattr(sys, "argv", [
        "main.py", "--fonte", "alibaba", "--busca", "relogio infantil", "--max-moq", "100", "--exportar"
    ])
    with patch("src.cli.main.DirectAlibabaClient.search", return_value=MOCK_ALIBABA_ITEMS), \
         patch("src.cli.main.export_to_excel", return_value=export_file) as mock_export:
        run()
        assert mock_export.called
        assert "oportunidades_alibaba.xlsx" in mock_export.call_args[0][1]

def test_cli_alibaba_filters_moq_out(monkeypatch):
    monkeypatch.setattr(sys, "argv", [
        "main.py", "--fonte", "alibaba", "--busca", "relogio", "--max-moq", "10"
    ])
    # Product requires MOQ 50, so with --max-moq 10 it should be filtered out
    with patch("src.cli.main.DirectAlibabaClient.search", return_value=MOCK_ALIBABA_ITEMS):
        try:
            run()
        except SystemExit as e:
            assert e.code == 0

def test_render_alibaba_table_runs_cleanly():
    records = [
        {
            "Produto": "Kids Watch Silicone LED",
            "Fornecedor": "Shenzhen Factory Ltd",
            "MOQ": 50,
            "Preço Unit. (R$)": 6.00,
            "Custo Unit. Final (R$)": 11.57,
            "Investimento Lote (R$)": 578.31,
            "Sugestão Venda (R$)": 26.29,
            "Lucro Líquido Lote (R$)": 405.00,
            "ROI (%)": 70.0,
            "Verified": True,
            "Trade Assurance": True,
            "Anos": 4,
            "Link": "https://alibaba.com/product/1.html"
        },
        {
            "Produto": "No Badges Product",
            "Fornecedor": "Unknown Seller",
            "MOQ": 10,
            "Preço Unit. (R$)": 20.00,
            "Custo Unit. Final (R$)": 38.55,
            "Investimento Lote (R$)": 385.54,
            "Sugestão Venda (R$)": 87.62,
            "Lucro Líquido Lote (R$)": 270.00,
            "ROI (%)": 70.0,
            "Verified": False,
            "Trade Assurance": False,
            "Anos": 0,
            "Link": ""
        }
    ]
    render_alibaba_table(records)

def test_export_to_excel_alibaba(tmp_path):
    out_file = str(tmp_path / "oportunidades_alibaba.xlsx")
    records = [
        {
            "Produto": "Kids Watch Silicone LED",
            "Fornecedor": "Shenzhen Factory Ltd",
            "MOQ": 50,
            "Preço Unit. (R$)": 6.00,
            "Custo Unit. Final (R$)": 11.57,
            "Investimento Lote (R$)": 578.31,
            "Sugestão Venda (R$)": 26.29,
            "Lucro Líquido Lote (R$)": 405.00,
            "ROI (%)": 70.0,
            "Verified": True,
            "Trade Assurance": True,
            "Anos": 4,
            "Link": "https://alibaba.com/product/1.html"
        }
    ]
    path = export_to_excel(records, out_file)
    assert os.path.exists(path)
    df = pd.read_excel(path)
    assert len(df) == 1
    assert df.iloc[0]["Produto"] == "Kids Watch Silicone LED"
    assert df.iloc[0]["MOQ"] == 50
    assert df.iloc[0]["Fornecedor"] == "Shenzhen Factory Ltd"

def test_cli_alibaba_no_items(monkeypatch):
    monkeypatch.setattr(sys, "argv", [
        "main.py", "--fonte", "alibaba", "--busca", "relogio inexistente"
    ])
    with patch("src.cli.main.DirectAlibabaClient.search", return_value=[]):
        try:
            run()
        except SystemExit as e:
            assert e.code == 0

def test_cli_alibaba_max_custo_filter(monkeypatch):
    monkeypatch.setattr(sys, "argv", [
        "main.py", "--fonte", "alibaba", "--busca", "relogio", "--max-custo", "5.0"
    ])
    # Unit landed cost will be ~11.57, so with --max-custo 5.0 it should be skipped
    with patch("src.cli.main.DirectAlibabaClient.search", return_value=MOCK_ALIBABA_ITEMS):
        try:
            run()
        except SystemExit as e:
            assert e.code == 0
