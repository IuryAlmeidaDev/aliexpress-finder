import pytest
from src.config import Config
from src.filters.pipeline import FilterPipeline
from src.finance.taxes import calculate_import_taxes
from src.finance.margins import simulate_resale
from src.cli.exporter import export_to_excel
import os
import pandas as pd

def test_full_pipeline_integration(tmp_path):
    mock_items = [
        {"title": "Strap only for Diver Watch", "price": 25.0, "rating": 4.9, "sales": 100, "url": "http://ali/1"},
        {"title": "Quartz Sapphire Watch", "price": 120.0, "rating": 4.8, "sales": 80, "url": "http://ali/2"},
        {"title": "Tandorio 39mm Automatic Diver Sapphire Glass Sterile Dial", "price": 220.0, "rating": 4.8, "sales": 45, "url": "http://ali/3"},
    ]

    pipeline = FilterPipeline(min_rating=4.5, min_sales=10)
    passed = pipeline.filter_products(
        items=mock_items,
        search_query="relogio automatico",
        include_terms=["safira", "sterile"],
        exclude_terms=["quartz"]
    )
    assert len(passed) == 1
    winner = passed[0]
    assert "Tandorio" in winner["title"]

    taxes = calculate_import_taxes(winner["price"], shipping_fee_brl=0.0, usd_brl_rate=5.50, icms_rate=0.17)
    assert taxes.total_landed_cost_brl > winner["price"]
    assert taxes.import_tax_brl > 0
    assert taxes.icms_tax_brl > 0

    margins = simulate_resale(taxes.total_landed_cost_brl, target_margin_pct=0.40, marketplace_fee_pct=0.16)
    assert margins.net_profit_brl > 0
    assert margins.suggested_sale_price_brl > taxes.total_landed_cost_brl
    assert margins.roi_pct > 0

    # Test export of integrated record
    record = {
        "Produto": winner["title"],
        "Preço Ali (R$)": winner["price"],
        "Impostos BR (R$)": taxes.total_taxes_brl,
        "Custo Final (R$)": taxes.total_landed_cost_brl,
        "Sugestão Venda (R$)": margins.suggested_sale_price_brl,
        "Lucro Líquido (R$)": margins.net_profit_brl,
        "ROI (%)": margins.roi_pct,
        "Avaliação": winner["rating"],
        "Link": winner["url"],
    }
    out_file = str(tmp_path / "integration_export.xlsx")
    export_to_excel([record], out_file)
    assert os.path.exists(out_file)
    df = pd.read_excel(out_file)
    assert len(df) == 1
    assert df.iloc[0]["Produto"] == winner["title"]
