from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from .config import FUNDAMENTAL_WEIGHTS, LIQUIDITY_WEIGHTS


def _bounded(value: object, low: float, high: float) -> float | None:
    """Normalize a metric to 0-100 without inventing a score for missing data."""
    if value is None or pd.isna(value):
        return None
    return float(np.clip((float(value) - low) / (high - low) * 100, 0, 100))


def _debt_score(value: object) -> float | None:
    """Invert debt-to-equity so lower leverage receives a higher liquidity score."""
    if value is None or pd.isna(value):
        return None
    return float(np.clip(100 - float(value) / 2, 0, 100))


def weighted_score(
    metrics: Mapping[str, object],
    weights: Mapping[str, float],
    transforms: Mapping[str, tuple[float, float] | str],
) -> tuple[float | None, float, dict[str, float | None]]:
    """Return score, weighted evidence coverage, and inspectable component scores."""
    used_weight = 0.0
    weighted_sum = 0.0
    components: dict[str, float | None] = {}

    for name, weight in weights.items():
        transform = transforms[name]
        component = (
            _debt_score(metrics.get(name))
            if transform == "debt"
            else _bounded(metrics.get(name), *transform)
        )
        components[name] = component
        if component is not None:
            weighted_sum += component * weight
            used_weight += weight

    if used_weight == 0:
        return None, 0.0, components
    return weighted_sum / used_weight, used_weight / sum(weights.values()), components


def score_company(metrics: Mapping[str, object]) -> dict[str, object]:
    """Calculate transparent fundamental and liquidity scores from provider metrics."""
    fundamental, fundamental_coverage, fundamental_components = weighted_score(
        metrics,
        FUNDAMENTAL_WEIGHTS,
        {
            "returnOnEquity": (-0.10, 0.35),
            "operatingMargins": (-0.10, 0.40),
            "profitMargins": (-0.10, 0.30),
            "revenueGrowth": (-0.30, 0.50),
        },
    )
    liquidity, liquidity_coverage, liquidity_components = weighted_score(
        metrics,
        LIQUIDITY_WEIGHTS,
        {
            "currentRatio": (0.5, 3.0),
            "quickRatio": (0.25, 2.5),
            "debtToEquity": "debt",
        },
    )

    available_scores = [score for score in (fundamental, liquidity) if score is not None]
    return {
        "fundamental_score": fundamental,
        "liquidity_score": liquidity,
        "overall_score": float(np.mean(available_scores)) if available_scores else None,
        "coverage": (fundamental_coverage + liquidity_coverage) / 2,
        "fundamental_coverage": fundamental_coverage,
        "liquidity_coverage": liquidity_coverage,
        "fundamental_components": fundamental_components,
        "liquidity_components": liquidity_components,
    }


def coverage_aware_percentiles(
    frame: pd.DataFrame,
    score_column: str = "overall_score",
    coverage_column: str = "coverage",
    minimum_coverage: float = 0.50,
) -> pd.DataFrame:
    """Rank only peers that have enough observed scoring evidence."""
    result = frame.copy()
    eligible = result[score_column].notna() & (result[coverage_column] >= minimum_coverage)
    result["percentile"] = np.nan
    if eligible.any():
        result.loc[eligible, "percentile"] = (
            result.loc[eligible, score_column].rank(pct=True) * 100
        )
    result["percentile_eligible"] = eligible
    return result


def score_peer_frame(
    frame: pd.DataFrame, minimum_coverage: float = 0.50
) -> pd.DataFrame:
    """Score each peer and attach coverage-aware percentile display fields."""
    records = []
    for _, row in frame.iterrows():
        scored = score_company(row.to_dict())
        records.append({
            **row.to_dict(),
            **{key: value for key, value in scored.items() if not key.endswith("components")},
        })
    return coverage_aware_percentiles(
        pd.DataFrame(records), minimum_coverage=minimum_coverage
    )
