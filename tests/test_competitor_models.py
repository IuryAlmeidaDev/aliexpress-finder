import pytest
from src.competitors.models import TargetProduct, CompetitorProduct, MarketDossier

def test_target_product_creation():
    target = TargetProduct(
        title="Relógio Masculino Automático Aço Safira",
        url="https://lojaexemplo.com.br/relogio",
        reference_price_brl=350.00,
        clean_query="relogio masculino automatico aco safira",
        category="Relógios",
        specs={"material": "aço 316l", "vidro": "safira"},
        kit_items=["estojo de luxo", "manual em portugues"]
    )
    assert target.title == "Relógio Masculino Automático Aço Safira"
    assert target.reference_price_brl == 350.00
    assert "estojo de luxo" in target.kit_items
    assert target.specs["vidro"] == "safira"

def test_target_product_defaults():
    target = TargetProduct(
        title="Óculos Quadrado",
        reference_price_brl=50.0,
        clean_query="oculos quadrado"
    )
    assert target.url is None
    assert target.category == "Geral"
    assert target.specs == {}
    assert target.kit_items == []

def test_competitor_product_creation():
    comp = CompetitorProduct(
        title="Óculos De Sol Masculino Quadrado Acetato Uv400",
        url="https://produto.mercadolivre.com.br/MLB-123456",
        store_name="Ótica Alfa",
        platform="Mercado Livre",
        price_brl=58.11,
        original_price_brl=149.90,
        shipping_type="Full",
        rating=4.7,
        reviews_count=2600,
        sales_volume="+10 mil vendidos",
        kit_items=["estojo rígido", "flanela de microfibra"],
        differentials=["Garantia 90 dias", "Proteção UV400"]
    )
    assert comp.price_brl == 58.11
    assert comp.shipping_type == "Full"
    assert len(comp.kit_items) == 2
    assert "Garantia 90 dias" in comp.differentials

def test_market_dossier_creation():
    target = TargetProduct(
        title="Óculos de Sol",
        reference_price_brl=60.0,
        clean_query="oculos de sol"
    )
    comp1 = CompetitorProduct(
        title="Óculos A",
        url="https://ml.com/1",
        store_name="Loja 1",
        platform="Mercado Livre",
        price_brl=50.0,
        shipping_type="Full"
    )
    comp2 = CompetitorProduct(
        title="Óculos B",
        url="https://ml.com/2",
        store_name="Loja 2",
        platform="Mercado Livre",
        price_brl=70.0,
        shipping_type="Normal"
    )

    dossier = MarketDossier(
        target=target,
        competitors=[comp1, comp2],
        min_competitor_price=50.0,
        max_competitor_price=70.0,
        avg_competitor_price=60.0,
        median_competitor_price=60.0,
        full_shipping_share_pct=50.0,
        common_kit_items=["estojo"],
        market_gaps=["Poucos concorrentes oferecem flanela personalizada"],
        target_fob_china_usd=1.80
    )
    assert len(dossier.competitors) == 2
    assert dossier.avg_competitor_price == 60.0
    assert dossier.target_fob_china_usd == 1.80
    assert dossier.usd_rate == 5.50
    assert dossier.target_fob_china_brl == round(1.80 * 5.50, 2)
