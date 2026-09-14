import os
import pandas as pd
from src.filters.alibaba_pipeline import AlibabaFilterPipeline
from src.finance.wholesale import calculate_wholesale_batch_costs, simulate_wholesale_resale
from src.cli.exporter import export_to_excel

def test_full_alibaba_pipeline_integration(tmp_path):
    raw_items = [
        {
            "id": "1",
            "title": "Custom Kids LED Watch Silicone Waterproof",
            "price": 5.0,
            "moq": 50,
            "is_verified": True,
            "has_trade_assurance": True,
            "years_in_business": 3,
            "supplier_name": "Shenzhen Smart Tech Co",
            "url": "https://alibaba.com/product/1.html"
        },
        {
            "id": "2",
            "title": "Expensive Gold Watch Luxury",
            "price": 50.0,
            "moq": 500,
            "is_verified": False,
            "has_trade_assurance": False,
            "years_in_business": 1,
            "supplier_name": "Gold Co",
            "url": "https://alibaba.com/product/2.html"
        },
        {
            "id": "3",
            "title": "Silicone Strap Band Replacement",
            "price": 1.0,
            "moq": 20,
            "is_verified": True,
            "has_trade_assurance": True,
            "years_in_business": 5,
            "supplier_name": "Strap Factory",
            "url": "https://alibaba.com/product/3.html"
        }
    ]

    # Pipeline: max_moq 100, verified only, trade assurance only, exclude straps
    pipeline = AlibabaFilterPipeline(max_moq=100, only_verified=True, only_trade_assurance=True)
    filtered = pipeline.filter_products(
        raw_items,
        search_query="watch",
        include_terms=["silicone"],
        exclude_terms=["strap"]
    )
    assert len(filtered) == 1

    item = filtered[0]
    assert item["title"] == "Custom Kids LED Watch Silicone Waterproof"

    # Wholesale finance calculations
    costs = calculate_wholesale_batch_costs(unit_price_brl=item["price"], moq=item["moq"], icms_rate=0.17)
    resale = simulate_wholesale_resale(
        batch_landed_cost_brl=costs.total_batch_landed_cost_brl,
        moq=item["moq"],
        target_margin_pct=0.40,
        marketplace_fee_pct=0.16
    )

    record = [{
        "Produto": item["title"],
        "Fornecedor": item["supplier_name"],
        "MOQ": item["moq"],
        "Preço Unit. (R$)": item["price"],
        "Custo Unit. Final (R$)": costs.unit_landed_cost_brl,
        "Investimento Lote (R$)": costs.total_batch_landed_cost_brl,
        "Sugestão Venda (R$)": resale.unit_sale_price_brl,
        "Lucro Líquido Lote (R$)": resale.projected_net_profit_brl,
        "ROI (%)": resale.roi_pct,
        "Verified": item["is_verified"],
        "Trade Assurance": item["has_trade_assurance"],
        "Anos": item["years_in_business"],
        "Link": item["url"]
    }]

    out_file = str(tmp_path / "oportunidades_alibaba.xlsx")
    out = export_to_excel(record, out_file)
    assert os.path.exists(out)

    df = pd.read_excel(out)
    assert len(df) == 1
    assert df.iloc[0]["Produto"] == "Custom Kids LED Watch Silicone Waterproof"
    assert df.iloc[0]["MOQ"] == 50
    assert df.iloc[0]["Investimento Lote (R$)"] > 0
    assert df.iloc[0]["Lucro Líquido Lote (R$)"] > 0
