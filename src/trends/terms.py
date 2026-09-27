# src/trends/terms.py
"""Default search terms for the Trend Radar daily collection."""
from __future__ import annotations

DEFAULT_TERMS: list[dict] = [
    # Eletrônicos
    {"term": "wireless earbuds", "category": "Eletrônicos", "source": "both"},
    {"term": "phone holder", "category": "Eletrônicos", "source": "both"},
    {"term": "portable charger", "category": "Eletrônicos", "source": "both"},
    {"term": "led strip lights", "category": "Eletrônicos", "source": "both"},
    {"term": "smart watch", "category": "Eletrônicos", "source": "both"},
    {"term": "bluetooth speaker", "category": "Eletrônicos", "source": "both"},
    {"term": "ring light", "category": "Eletrônicos", "source": "both"},
    {"term": "mini projector", "category": "Eletrônicos", "source": "both"},
    # Casa & Cozinha
    {"term": "kitchen gadget", "category": "Casa & Cozinha", "source": "both"},
    {"term": "organizer storage", "category": "Casa & Cozinha", "source": "both"},
    {"term": "silicone mold", "category": "Casa & Cozinha", "source": "both"},
    {"term": "electric kettle", "category": "Casa & Cozinha", "source": "both"},
    {"term": "mini blender", "category": "Casa & Cozinha", "source": "both"},
    {"term": "vacuum sealer", "category": "Casa & Cozinha", "source": "both"},
    {"term": "spice rack", "category": "Casa & Cozinha", "source": "both"},
    {"term": "coffee accessories", "category": "Casa & Cozinha", "source": "both"},
    # Beleza & Saúde
    {"term": "hair straightener brush", "category": "Beleza & Saúde", "source": "both"},
    {"term": "facial massager", "category": "Beleza & Saúde", "source": "both"},
    {"term": "nail art kit", "category": "Beleza & Saúde", "source": "both"},
    {"term": "makeup organizer", "category": "Beleza & Saúde", "source": "both"},
    {"term": "teeth whitening", "category": "Beleza & Saúde", "source": "both"},
    {"term": "scalp massager", "category": "Beleza & Saúde", "source": "both"},
    {"term": "beauty blender", "category": "Beleza & Saúde", "source": "both"},
    {"term": "lash curler", "category": "Beleza & Saúde", "source": "both"},
    # Moda & Acessórios
    {"term": "polarized sunglasses", "category": "Moda & Acessórios", "source": "both"},
    {"term": "automatic watch", "category": "Moda & Acessórios", "source": "both"},
    {"term": "crossbody bag", "category": "Moda & Acessórios", "source": "both"},
    {"term": "minimalist wallet", "category": "Moda & Acessórios", "source": "both"},
    {"term": "stainless steel ring", "category": "Moda & Acessórios", "source": "both"},
    {"term": "silk scarf", "category": "Moda & Acessórios", "source": "both"},
    {"term": "bucket hat", "category": "Moda & Acessórios", "source": "both"},
    # Ferramentas
    {"term": "laser level", "category": "Ferramentas", "source": "both"},
    {"term": "electric screwdriver", "category": "Ferramentas", "source": "both"},
    {"term": "soldering kit", "category": "Ferramentas", "source": "both"},
    {"term": "digital caliper", "category": "Ferramentas", "source": "both"},
    {"term": "heat gun", "category": "Ferramentas", "source": "both"},
    {"term": "wire stripper", "category": "Ferramentas", "source": "both"},
    {"term": "multimeter", "category": "Ferramentas", "source": "both"},
    # Pet
    {"term": "automatic pet feeder", "category": "Pet", "source": "both"},
    {"term": "dog harness", "category": "Pet", "source": "both"},
    {"term": "cat toy interactive", "category": "Pet", "source": "both"},
    {"term": "pet grooming", "category": "Pet", "source": "both"},
    {"term": "dog training collar", "category": "Pet", "source": "both"},
    {"term": "cat water fountain", "category": "Pet", "source": "both"},
    # Esporte & Outdoor
    {"term": "resistance bands", "category": "Esporte & Outdoor", "source": "both"},
    {"term": "jump rope", "category": "Esporte & Outdoor", "source": "both"},
    {"term": "hiking backpack", "category": "Esporte & Outdoor", "source": "both"},
    {"term": "camping light", "category": "Esporte & Outdoor", "source": "both"},
    {"term": "yoga mat", "category": "Esporte & Outdoor", "source": "both"},
    {"term": "fishing lure set", "category": "Esporte & Outdoor", "source": "both"},
    {"term": "bike light", "category": "Esporte & Outdoor", "source": "both"},
    # Bebê & Criança
    {"term": "baby carrier", "category": "Bebê & Criança", "source": "both"},
    {"term": "educational toy", "category": "Bebê & Criança", "source": "both"},
    {"term": "kids tablet", "category": "Bebê & Criança", "source": "both"},
    {"term": "baby monitor", "category": "Bebê & Criança", "source": "both"},
    {"term": "stroller organizer", "category": "Bebê & Criança", "source": "both"},
    {"term": "teething toy", "category": "Bebê & Criança", "source": "both"},
]


def get_default_terms() -> list[dict]:
    """Return a copy of the default terms list."""
    return [dict(t) for t in DEFAULT_TERMS]
