from src.mercado_livre.brand import analyze_brand_potential
from src.mercado_livre.models import RadarProduct
from src.mercado_livre.scoring import score_product


def test_brand_score_requires_evidence_and_reports_coverage():
    product = RadarProduct(
        entity_id="MLB1", entity_type="ITEM", category_id="MLB10",
        title="Caderno personalizado com logo", rank=1,
        attributes={"BRAND": "Genérica", "COLOR": "Azul", "MATERIAL": "Papel"},
        review_average=4.8, review_count=100,
        review_texts=["Embalagem amassada"] * 3,
    )
    evidence = analyze_brand_potential(product)
    score = score_product(product, evidence, 100, 4.5)
    assert score.demand_coverage == 80.0
    assert score.brand_coverage == 100.0
    assert score.priority is True
    assert score.brand_score > 70
    assert any("embalagem" in reason.lower() for reason in score.brand_reasons)


def test_missing_data_is_not_zero_evidence():
    product = RadarProduct("MLB2", "PRODUCT", "MLB10", "Produto desconhecido", rank=10)
    evidence = analyze_brand_potential(product)
    score = score_product(product, evidence, None, None)
    assert score.demand_coverage == 40.0
    assert score.brand_coverage == 0.0
    assert score.priority is False
