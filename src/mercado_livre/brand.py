from __future__ import annotations

import re
import unicodedata
from collections import defaultdict

from .models import BrandEvidence, RadarProduct


GENERIC_BRANDS = {"", "generico", "generica", "sem marca", "no brand", "unbranded", "outra"}
VARIANT_ATTRIBUTES = {"COLOR", "MATERIAL", "SIZE", "LENGTH", "WIDTH", "MODEL", "DESIGN"}
CUSTOM_TERMS = ("personaliz", "custom", "gravacao", "estampa", "bordado", "logo")
COMPLAINT_THEMES = {
    "material ou acabamento": ("material", "acabamento", "fragil", "quebrou", "descasc", "costura"),
    "tamanho ou ajuste": ("tamanho", "pequeno", "grande", "apertado", "largo", "ajuste"),
    "embalagem": ("embalagem", "amassad", "caixa", "proteca"),
    "durabilidade": ("durabilidade", "parou", "defeito", "estrag", "nao funciona"),
    "aparência": ("cor diferente", "foto", "aparencia", "bonito", "feio"),
}


def normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in value if not unicodedata.combining(ch))


def analyze_brand_potential(product: RadarProduct) -> BrandEvidence:
    normalized_title = normalize(product.title)
    has_brand_attribute = "BRAND" in product.attributes
    brand = normalize(product.attributes.get("BRAND", ""))
    generic_signals: list[str] = []
    counterpoints: list[str] = []
    if not has_brand_attribute:
        generic = None
        counterpoints.append("marca não informada nos atributos consultados")
    elif brand in GENERIC_BRANDS:
        generic = 1.0
        generic_signals.append("marca ausente ou declarada como genérica")
    else:
        generic = 0.0
        counterpoints.append(f"produto associado à marca {product.attributes.get('BRAND')}")

    theme_hits: dict[str, list[str]] = defaultdict(list)
    for text in product.review_texts:
        normalized = normalize(text)
        for theme, terms in COMPLAINT_THEMES.items():
            if any(term in normalized for term in terms):
                theme_hits[theme].append(text)
    recurring = {theme: texts for theme, texts in theme_hits.items() if len(texts) >= 3}
    reviews_observed = product.review_count is not None
    problems = 1.0 if recurring else (0.0 if reviews_observed else None)
    problem_evidence = [
        f"{theme}: {len(texts)} menções em {len(product.review_texts)} avaliações consultadas"
        for theme, texts in recurring.items()
    ]

    custom_signal = any(term in normalized_title for term in CUSTOM_TERMS)
    useful_attributes = [
        key for key, value in product.attributes.items()
        if value and key not in {"BRAND", "GTIN", "EAN"}
    ]
    differentiation_evidence: list[str] = []
    if recurring:
        differentiation = 1.0
        differentiation_evidence.append("há problema recorrente que permite uma melhoria concreta")
    elif custom_signal:
        differentiation = 1.0
        differentiation_evidence.append("o anúncio menciona personalização, gravação, estampa ou logo")
    elif len(useful_attributes) >= 4:
        differentiation = 0.5
        differentiation_evidence.append("atributos de produto permitem diferenciar especificação e acabamento")
    elif product.attributes:
        differentiation = 0.0
    else:
        differentiation = None

    variant_keys = [key for key in product.attributes if key in VARIANT_ATTRIBUTES]
    if len(variant_keys) >= 2:
        line_potential = 1.0
        line_evidence = [f"variações estruturadas disponíveis: {', '.join(variant_keys[:5])}"]
    elif variant_keys:
        line_potential = 0.5
        line_evidence = [f"uma dimensão de variação disponível: {variant_keys[0]}"]
    elif product.attributes:
        line_potential = 0.0
        line_evidence = []
    else:
        line_potential = None
        line_evidence = []

    if not product.review_texts and reviews_observed:
        counterpoints.append("nenhum comentário textual disponível na amostra consultada")
    if product.review_count is not None and product.review_count < 20:
        counterpoints.append("base pequena de avaliações")

    return BrandEvidence(
        differentiation=differentiation,
        problems=problems,
        generic=generic,
        line_potential=line_potential,
        differentiation_evidence=differentiation_evidence,
        problem_evidence=problem_evidence,
        generic_evidence=generic_signals,
        line_evidence=line_evidence,
        counterpoints=counterpoints,
    )
