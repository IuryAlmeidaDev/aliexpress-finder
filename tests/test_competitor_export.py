import os
import pytest
import pandas as pd
from src.competitors.models import TargetProduct, CompetitorProduct, MarketDossier
from src.competitors.exporter import export_dossier_markdown, export_competitors_excel

@pytest.fixture
def sample_dossier():
    target = TargetProduct(
        title="Óculos De Sol Masculino Quadrado",
        url="https://loja.com/oculos",
        reference_price_brl=60.0,
        clean_query="oculos de sol quadrado",
        kit_items=["estojo rígido"]
    )
    comp1 = CompetitorProduct(
        title="Óculos Concorrente A",
        url="https://ml.com/1",
        store_name="Loja Alfa",
        platform="Mercado Livre",
        price_brl=49.90,
        shipping_type="Full",
        kit_items=["estojo", "flanela"],
        differentials=["Entrega Full", "UV400"]
    )
    comp2 = CompetitorProduct(
        title="Óculos Concorrente B",
        url="https://ml.com/2",
        store_name="Beta Shop",
        platform="Mercado Livre",
        price_brl=69.90,
        shipping_type="Frete Grátis",
        kit_items=[],
        differentials=["Frete Grátis"]
    )
    return MarketDossier(
        target=target,
        competitors=[comp1, comp2],
        min_competitor_price=49.90,
        max_competitor_price=69.90,
        avg_competitor_price=59.90,
        median_competitor_price=59.90,
        full_shipping_share_pct=50.0,
        common_kit_items=["estojo"],
        market_gaps=["Oportunidade de incluir flanela personalizada."],
        target_fob_china_usd=1.85,
        recommended_china_suppliers=[
            {"title": "Factory Sunglasses Yiwu", "price": "US$ 1.20", "moq": "50 un", "url": "https://alibaba.com/sample"}
        ]
    )

def test_export_dossier_markdown(sample_dossier, tmp_path):
    output_path = tmp_path / "dossie_mercado.md"
    export_dossier_markdown(sample_dossier, str(output_path))

    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "# Dossiê de Inteligência Competitiva" in content
    assert "Óculos De Sol Masculino Quadrado" in content
    assert "Loja Alfa" in content
    assert "R$ 49,90" in content or "49.90" in content
    assert "Factory Sunglasses Yiwu" in content

def test_export_competitors_excel(sample_dossier, tmp_path):
    output_path = tmp_path / "benchmarking_concorrencia.xlsx"
    export_competitors_excel(sample_dossier, str(output_path))

    assert output_path.exists()
    excel_file = pd.ExcelFile(str(output_path))
    assert "Concorrentes" in excel_file.sheet_names
    assert "Resumo e Estratégia" in excel_file.sheet_names

    df_comp = pd.read_excel(excel_file, sheet_name="Concorrentes")
    assert len(df_comp) == 2
    assert "Loja Alfa" in df_comp["Loja / Vendedor"].values
