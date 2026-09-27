# tests/test_trend_terms.py
from src.trends.terms import DEFAULT_TERMS, get_default_terms


def test_default_terms_not_empty():
    assert len(DEFAULT_TERMS) >= 50


def test_default_terms_have_required_fields():
    for t in DEFAULT_TERMS:
        assert "term" in t and isinstance(t["term"], str) and len(t["term"]) > 0
        assert "category" in t and isinstance(t["category"], str) and len(t["category"]) > 0
        assert "source" in t and t["source"] in ("ali", "alibaba", "both")


def test_default_terms_unique():
    terms = [t["term"] for t in DEFAULT_TERMS]
    assert len(terms) == len(set(terms)), "Duplicate terms found"


def test_default_terms_cover_expected_categories():
    categories = {t["category"] for t in DEFAULT_TERMS}
    expected = {"Eletrônicos", "Casa & Cozinha", "Beleza & Saúde",
                "Moda & Acessórios", "Ferramentas", "Pet",
                "Esporte & Outdoor", "Bebê & Criança"}
    assert expected.issubset(categories), f"Missing categories: {expected - categories}"


def test_get_default_terms_returns_copy():
    a = get_default_terms()
    b = get_default_terms()
    assert a == b
    assert a is not b
