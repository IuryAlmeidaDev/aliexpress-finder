from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class RadarProduct:
    entity_id: str
    entity_type: str
    category_id: str
    title: str
    url: str = ""
    rank: Optional[int] = None
    catalog_product_id: Optional[str] = None
    item_id: Optional[str] = None
    price: Optional[float] = None
    sold_quantity: Optional[int] = None
    attributes: dict[str, str] = field(default_factory=dict)
    review_average: Optional[float] = None
    review_count: Optional[int] = None
    review_texts: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def entity_key(self) -> str:
        return f"{self.entity_type}:{self.entity_id}"


@dataclass
class BrandEvidence:
    differentiation: Optional[float]
    problems: Optional[float]
    generic: Optional[float]
    line_potential: Optional[float]
    differentiation_evidence: list[str] = field(default_factory=list)
    problem_evidence: list[str] = field(default_factory=list)
    generic_evidence: list[str] = field(default_factory=list)
    line_evidence: list[str] = field(default_factory=list)
    counterpoints: list[str] = field(default_factory=list)


@dataclass
class RadarScore:
    demand_score: float
    demand_coverage: float
    brand_score: float
    brand_coverage: float
    combined_score: float
    priority: bool
    demand_reasons: list[str]
    brand_reasons: list[str]
    counterpoints: list[str]
    evidence: BrandEvidence
