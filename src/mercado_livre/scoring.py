from __future__ import annotations

import math
from typing import Any, Optional

from .models import BrandEvidence, RadarProduct, RadarScore


def _weighted(values: dict[str, tuple[Optional[float], float]]) -> tuple[float, float]:
    observed = [(value, weight) for value, weight in values.values() if value is not None]
    covered = sum(weight for _, weight in observed)
    if not observed or covered <= 0:
        return 0.0, 0.0
    score = sum(float(value) * weight for value, weight in observed) / covered
    return round(score * 100, 1), round(covered * 100, 1)


def score_product(
    product: RadarProduct,
    evidence: BrandEvidence,
    category_max_reviews: Optional[int],
    category_rating_mean: Optional[float],
    previous: Optional[dict[str, Any]] = None,
) -> RadarScore:
    rank_value = None if product.rank is None else max(0.0, min(1.0, 1 - (product.rank - 1) / 19))
    volume_value = None
    if product.review_count is not None and category_max_reviews and category_max_reviews > 0:
        volume_value = math.log1p(product.review_count) / math.log1p(category_max_reviews)

    satisfaction_value = None
    if product.review_average is not None and product.review_count is not None and category_rating_mean is not None:
        smoothed = (
            product.review_average * product.review_count + category_rating_mean * 20
        ) / (product.review_count + 20)
        satisfaction_value = max(0.0, min(1.0, (smoothed - 1.0) / 4.0))

    evolution_value = None
    if previous:
        old_rank = previous.get("rank")
        old_reviews = previous.get("review_count")
        parts = []
        if old_rank and product.rank:
            parts.append(max(0.0, min(1.0, 0.5 + (old_rank - product.rank) / 20)))
        if old_reviews is not None and product.review_count is not None:
            delta = product.review_count - int(old_reviews)
            parts.append(max(0.0, min(1.0, 0.5 + delta / max(int(old_reviews), 10))))
        if parts:
            evolution_value = sum(parts) / len(parts)

    demand_score, demand_coverage = _weighted({
        "rank": (rank_value, 0.40),
        "volume": (volume_value, 0.20),
        "satisfaction": (satisfaction_value, 0.20),
        "evolution": (evolution_value, 0.20),
    })
    brand_score, brand_coverage = _weighted({
        "differentiation": (evidence.differentiation, 0.40),
        "problems": (evidence.problems, 0.25),
        "generic": (evidence.generic, 0.20),
        "line": (evidence.line_potential, 0.15),
    })
    combined = round(math.sqrt(demand_score * brand_score), 1) if demand_score and brand_score else 0.0
    priority = (
        demand_coverage >= 60
        and brand_coverage >= 60
        and bool(evidence.differentiation_evidence)
    )

    demand_reasons = []
    if product.rank is not None:
        demand_reasons.append(f"posição {product.rank} entre os mais vendidos da categoria")
    if product.review_count is not None:
        demand_reasons.append(f"{product.review_count} avaliações; média {product.review_average or 0:.1f}")
    demand_reasons.append("histórico comparável disponível" if evolution_value is not None else "histórico semanal ainda insuficiente")
    brand_reasons = (
        evidence.differentiation_evidence
        + evidence.problem_evidence
        + evidence.generic_evidence
        + evidence.line_evidence
    )
    return RadarScore(
        demand_score=demand_score,
        demand_coverage=demand_coverage,
        brand_score=brand_score,
        brand_coverage=brand_coverage,
        combined_score=combined,
        priority=priority,
        demand_reasons=demand_reasons,
        brand_reasons=brand_reasons,
        counterpoints=evidence.counterpoints,
        evidence=evidence,
    )
