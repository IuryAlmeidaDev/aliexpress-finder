"""Trend Score (0-100) and strategic classification."""
from __future__ import annotations

from .models import (
    TrendVelocity,
    STRATEGY_OCEANO_AZUL, STRATEGY_TENDENCIA,
    STRATEGY_EMERGENTE, STRATEGY_SATURADO, STRATEGY_PENDENTE,
)

# Weight distribution
W_VELOCITY = 0.40
W_VACUUM = 0.35
W_VIABILITY = 0.25

# Normalization caps
MAX_COMPETITORS_CAP = 50
MAX_MARGIN_CAP = 50.0


def calculate_trend_score(
    velocity: TrendVelocity,
    ml_competitors: int | None,
    net_margin_pct: float | None,
    max_velocity_in_category: int,
) -> tuple[float, str]:
    """Return (score 0-100, strategy string)."""

    # Velocity signal (0-100)
    if max_velocity_in_category > 0:
        vel_score = min(velocity.sales_velocity_7d / max_velocity_in_category, 1.0) * 100
    else:
        vel_score = 100.0 if velocity.sales_velocity_7d > 0 else 0.0

    # If ML data is missing, return PENDENTE with partial score
    if ml_competitors is None or net_margin_pct is None:
        partial = vel_score * W_VELOCITY
        return (round(min(max(partial, 0), 100), 1), STRATEGY_PENDENTE)

    # Vacuum signal (0-100): inverse of competitor count
    if ml_competitors <= 0:
        vac_score = 100.0
    elif ml_competitors >= MAX_COMPETITORS_CAP:
        vac_score = 0.0
    else:
        vac_score = (1.0 - ml_competitors / MAX_COMPETITORS_CAP) * 100

    # Viability signal (0-100): margin clamped
    if net_margin_pct <= 0:
        via_score = 0.0
    elif net_margin_pct >= MAX_MARGIN_CAP:
        via_score = 100.0
    else:
        via_score = (net_margin_pct / MAX_MARGIN_CAP) * 100

    score = vel_score * W_VELOCITY + vac_score * W_VACUUM + via_score * W_VIABILITY
    score = round(min(max(score, 0), 100), 1)

    if score >= 75:
        strategy = STRATEGY_OCEANO_AZUL
    elif score >= 50:
        strategy = STRATEGY_TENDENCIA
    elif score >= 25:
        strategy = STRATEGY_EMERGENTE
    else:
        strategy = STRATEGY_SATURADO

    return (score, strategy)
