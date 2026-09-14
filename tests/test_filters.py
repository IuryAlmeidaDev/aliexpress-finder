from src.filters.anti_trick import is_accessory_trick
from src.filters.semantic import matches_semantic_criteria
from src.filters.reputation import satisfies_reputation
from src.filters.pipeline import FilterPipeline

def test_anti_trick_accessory_detection():
    # Should flag accessory items disguised as watch listings
    assert is_accessory_trick("Silicone strap for watch band 20mm", main_query="relogio automatico") is True
    assert is_accessory_trick("Empty watch box display case", main_query="relogio") is True
    assert is_accessory_trick("Pagani Design Automatic Watch NH35", main_query="relogio automatico") is False

def test_anti_trick_when_searching_for_accessories():
    # Should NOT flag accessories when user explicitly searches for them
    assert is_accessory_trick("Leather watch strap 20mm", main_query="pulseira de couro") is False
    assert is_accessory_trick("Watch display case wooden", main_query="caixa para relogio") is False

def test_semantic_terms_inclusion_and_exclusion():
    item_title = "Tandorio 39mm Automatic Diver Watch Sapphire Glass Sterile Dial"
    assert matches_semantic_criteria(item_title, include_terms=["safira", "sterile"], exclude_terms=["quartz"]) is True
    
    quartz_item = "Luxury Quartz Watch Sapphire Glass"
    assert matches_semantic_criteria(quartz_item, include_terms=["safira"], exclude_terms=["quartz"]) is False

def test_semantic_synonyms_and_normalization():
    # Accent normalization and synonym mappings
    assert matches_semantic_criteria("Relógio Automático Aço 316L", include_terms=["aço", "automatico"], exclude_terms=[]) is True
    assert matches_semantic_criteria("Relogio Automatico Dial No Logo", include_terms=["sem logo"], exclude_terms=[]) is True

def test_reputation_filter():
    assert satisfies_reputation(rating=4.8, sales=150, min_rating=4.5, min_sales=10) is True
    assert satisfies_reputation(rating=4.2, sales=150, min_rating=4.5, min_sales=10) is False
    assert satisfies_reputation(rating=4.9, sales=2, min_rating=4.5, min_sales=10) is False

def test_reputation_boundaries():
    assert satisfies_reputation(rating=4.5, sales=10, min_rating=4.5, min_sales=10) is True
    assert satisfies_reputation(rating=4.49, sales=10, min_rating=4.5, min_sales=10) is False
    assert satisfies_reputation(rating=4.5, sales=9, min_rating=4.5, min_sales=10) is False

def test_filter_pipeline():
    pipeline = FilterPipeline()
    items = [
        {"title": "Watch Strap 20mm", "price": 15.0, "rating": 4.9, "sales": 100},
        {"title": "Quartz Watch Safira", "price": 80.0, "rating": 4.7, "sales": 50},
        {"title": "Relógio Automático Vidro Safira Sem Logo", "price": 250.0, "rating": 4.8, "sales": 35},
        {"title": "Relógio Automático Safira Sem Logo Loja Ruim", "price": 240.0, "rating": 3.9, "sales": 1},
    ]
    filtered = pipeline.filter_products(
        items=items,
        search_query="relogio automatico",
        include_terms=["safira", "sem logo"],
        exclude_terms=["quartz", "pulseira"]
    )
    assert len(filtered) == 1
    assert filtered[0]["title"] == "Relógio Automático Vidro Safira Sem Logo"

def test_filter_pipeline_empty_and_defaults():
    pipeline = FilterPipeline()
    assert pipeline.filter_products([], "relogio") == []
