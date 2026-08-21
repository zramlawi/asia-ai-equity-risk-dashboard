from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

from .config import MINIMUM_EVIDENCE_COVERAGE, PILLAR_FIELDS, PILLAR_WEIGHTS, REGIME_RULES


def _value(metrics: Mapping[str, object], name: str) -> float | None:
    value = metrics.get(name)
    eligible = metrics.get(f"{name}_eligible", True)
    if value is None or pd.isna(value) or eligible is False:
        return None
    return float(value)


def _bounded(value: float | None, low: float, high: float, invert: bool = False) -> float | None:
    if value is None:
        return None
    scaled = np.clip((value - low) / (high - low) * 100, 0, 100)
    return float(100 - scaled if invert else scaled)


def _score_metric(name: str, value: float | None) -> float | None:
    ranges = {
        "momentum_3m": (-0.35, 0.60, False), "momentum_6m": (-0.50, 1.00, False),
        "trailingPE": (5, 55, True), "forwardPE": (5, 45, True),
        "priceToBook": (0.5, 12, True), "enterpriseToEbitda": (3, 35, True),
        "returnOnEquity": (-0.10, 0.35, False), "operatingMargins": (-0.10, 0.40, False),
        "profitMargins": (-0.10, 0.30, False), "revenueGrowth": (-0.30, 0.50, False),
        "freeCashflow": (-1e10, 5e10, False), "relative_volume": (0.5, 3.0, False),
        "volume_growth": (-0.50, 1.00, False), "annual_volatility": (0.10, 0.80, True),
        "max_drawdown": (-0.70, 0.0, False), "debtToEquity": (0, 250, True),
    }
    low, high, invert = ranges[name]
    return _bounded(value, low, high, invert)


def _pillar_score(metrics: Mapping[str, object], pillar: str) -> tuple[float | None, float, dict[str, float | None]]:
    weights = PILLAR_FIELDS[pillar]
    total_weight = sum(weights.values())
    used_weight = 0.0
    weighted_sum = 0.0
    components: dict[str, float | None] = {}
    for name, weight in weights.items():
        candidate = _score_metric(name, _value(metrics, name))
        components[name] = candidate
        if candidate is not None:
            weighted_sum += candidate * weight
            used_weight += weight
    if used_weight == 0:
        return None, 0.0, components
    return weighted_sum / used_weight, used_weight / total_weight, components


def regime_adjustment(metrics: Mapping[str, object]) -> dict[str, object]:
    adjustments: list[dict[str, object]] = []
    volatility = _value(metrics, "annual_volatility")
    drawdown = _value(metrics, "max_drawdown")
    if volatility is not None and volatility > REGIME_RULES["elevated_volatility"]["threshold"]:
        adjustments.append({"rule": "elevated_volatility", "points": REGIME_RULES["elevated_volatility"]["adjustment"]})
    if drawdown is not None and drawdown < REGIME_RULES["stressed_drawdown"]["threshold"]:
        adjustments.append({"rule": "stressed_drawdown", "points": REGIME_RULES["stressed_drawdown"]["adjustment"]})
    return {
        "points": float(sum(item["points"] for item in adjustments)),
        "rules": [item["rule"] for item in adjustments],
        "details": adjustments,
    }


def score_company(metrics: Mapping[str, object]) -> dict[str, object]:
    pillar_results = {pillar: _pillar_score(metrics, pillar) for pillar in PILLAR_WEIGHTS}
    used_weight = sum(PILLAR_WEIGHTS[p] * pillar_results[p][1] for p in PILLAR_WEIGHTS)
    weighted_total = sum(
        PILLAR_WEIGHTS[p] * pillar_results[p][0] * pillar_results[p][1]
        for p in PILLAR_WEIGHTS
        if pillar_results[p][0] is not None
    )
    base_score = weighted_total / used_weight if used_weight else None
    regime = regime_adjustment(metrics)
    overall = min(100.0, base_score + regime["points"]) if base_score is not None else None
    contributions = {
        pillar: (PILLAR_WEIGHTS[pillar] * pillar_results[pillar][0] * pillar_results[pillar][1] / used_weight)
        if used_weight and pillar_results[pillar][0] is not None else None
        for pillar in PILLAR_WEIGHTS
    }
    result: dict[str, object] = {
        "overall_score": overall,
        "base_score": base_score,
        "coverage": used_weight,
        "scoring_eligible": bool(used_weight >= MINIMUM_EVIDENCE_COVERAGE and overall is not None),
        "regime_points": regime["points"],
        "regime_rules": ", ".join(regime["rules"]) if regime["rules"] else "none",
        "contributions": contributions,
    }
    for pillar, (score, coverage, components) in pillar_results.items():
        result[f"{pillar}_score"] = score
        result[f"{pillar}_coverage"] = coverage
        result[f"{pillar}_components"] = components
    return result


def coverage_aware_percentiles(
    frame: pd.DataFrame,
    score_column: str = "overall_score",
    coverage_column: str = "coverage",
    minimum_coverage: float = MINIMUM_EVIDENCE_COVERAGE,
) -> pd.DataFrame:
    result = frame.copy()
    eligible = result[score_column].notna() & (result[coverage_column] >= minimum_coverage)
    if "scoring_eligible" in result:
        eligible &= result["scoring_eligible"].fillna(False)
    result["percentile"] = np.nan
    if eligible.any():
        result.loc[eligible, "percentile"] = result.loc[eligible, score_column].rank(pct=True) * 100
    result["percentile_eligible"] = eligible
    return result


def historical_percentile(value: float | None, history: pd.Series) -> float | None:
    if value is None or history.dropna().empty:
        return None
    return float((history.dropna() <= value).mean() * 100)


def score_peer_frame(frame: pd.DataFrame, minimum_coverage: float = MINIMUM_EVIDENCE_COVERAGE) -> pd.DataFrame:
    records = []
    for _, row in frame.iterrows():
        scored = score_company(row.to_dict())
        flattened = {key: value for key, value in scored.items() if not key.endswith("_components") and key != "contributions"}
        records.append({**row.to_dict(), **flattened})
    return coverage_aware_percentiles(pd.DataFrame(records), minimum_coverage=minimum_coverage)


def contribution_frame(score: Mapping[str, object]) -> pd.DataFrame:
    contributions = score.get("contributions", {})
    return pd.DataFrame(
        [{"pillar": pillar.replace("_", " ").title(), "contribution": value} for pillar, value in contributions.items()]
    )
