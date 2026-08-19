"""Transparent scenario-based bubble-risk scoring utilities."""

from __future__ import annotations

import re
from typing import Iterable

import numpy as np
import pandas as pd

DEFAULTS = {
    "valuation": 0.55,
    "earnings": 0.45,
    "market": 0.50,
    "ai_exposure": 0.50,
}

ALIASES = {
    "valuation": ["valuation_risk", "valuation_score", "pe_percentile", "pe_premium", "valuation"],
    "earnings": ["earnings_risk", "earnings_score", "earnings_revision", "earnings"],
    "market": ["market_risk", "market_score", "volatility", "beta", "market"],
    "ai_exposure": ["ai_exposure", "ai_revenue_share", "ai_score", "ai"],
}


def _normalise(series: pd.Series, default: float) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    valid = values.dropna()
    if valid.empty:
        return pd.Series(default, index=series.index, dtype=float)
    low, high = float(valid.min()), float(valid.max())
    if low >= 0 and high <= 1:
        result = values
    elif low >= 0 and high <= 100:
        result = values / 100.0
    elif high > low:
        result = (values - low) / (high - low)
    else:
        result = pd.Series(0.5, index=series.index, dtype=float)
    return result.fillna(default).clip(0.0, 1.0)


def _column_for(frame: pd.DataFrame, candidates: Iterable[str]) -> str | None:
    normalised = {re.sub(r"[^a-z0-9]+", "_", str(c).strip().lower()).strip("_"): c for c in frame.columns}
    for candidate in candidates:
        key = re.sub(r"[^a-z0-9]+", "_", candidate.lower()).strip("_")
        if key in normalised:
            return normalised[key]
    return None


def factor_series(frame: pd.DataFrame, factor: str) -> pd.Series:
    column = _column_for(frame, ALIASES[factor])
    if column is None:
        return pd.Series(DEFAULTS[factor], index=frame.index, dtype=float)
    return _normalise(frame[column], DEFAULTS[factor])


def calculate_risk(
    frame: pd.DataFrame,
    market_shock: float = -0.15,
    valuation_compression: float = 0.20,
    earnings_shortfall: float = 0.15,
) -> pd.DataFrame:
    """Score each company using input factors and a user-defined downside scenario.

    Inputs are scaled to [0, 1]. Missing factor columns use documented neutral defaults,
    allowing the dashboard to run with a basic country/ticker/name universe.
    """
    if not -1.0 <= market_shock <= 0.0:
        raise ValueError("market_shock must be between -1.0 and 0.0")
    if not 0.0 <= valuation_compression <= 1.0:
        raise ValueError("valuation_compression must be between 0.0 and 1.0")
    if not 0.0 <= earnings_shortfall <= 1.0:
        raise ValueError("earnings_shortfall must be between 0.0 and 1.0")

    result = frame.copy()
    result["valuation_risk"] = factor_series(result, "valuation")
    result["earnings_risk"] = factor_series(result, "earnings")
    result["market_risk"] = factor_series(result, "market")
    result["ai_exposure"] = factor_series(result, "ai_exposure")

    scenario_intensity = min(1.0, abs(market_shock) / 0.40)
    scenario_intensity = 0.40 * scenario_intensity + 0.35 * valuation_compression + 0.25 * earnings_shortfall
    base_risk = (
        0.35 * result["valuation_risk"]
        + 0.25 * result["earnings_risk"]
        + 0.25 * result["market_risk"]
        + 0.15 * result["ai_exposure"]
    )
    result["risk_score"] = (100.0 * base_risk * (0.55 + 0.45 * scenario_intensity)).clip(0.0, 100.0)
    result["scenario_drawdown_pct"] = -(
        abs(market_shock) * (0.55 + 0.45 * result["market_risk"])
        + valuation_compression * (0.05 + 0.20 * result["valuation_risk"] * result["ai_exposure"])
        + earnings_shortfall * (0.03 + 0.12 * result["earnings_risk"] * result["ai_exposure"])
    ).clip(0.0, 1.0)
    result["risk_band"] = pd.cut(
        result["risk_score"],
        bins=[-np.inf, 35, 65, np.inf],
        labels=["Low", "Moderate", "High"],
    ).astype(str)
    return result


def country_summary(scored: pd.DataFrame) -> pd.DataFrame:
    if "country" not in scored.columns:
        raise ValueError("scored data must include a country column")
    summary = (
        scored.groupby("country", dropna=False)
        .agg(
            companies=("risk_score", "size"),
            average_risk_score=("risk_score", "mean"),
            average_scenario_drawdown=("scenario_drawdown_pct", "mean"),
            high_risk_share=("risk_band", lambda x: (x == "High").mean()),
        )
        .reset_index()
    )
    return summary.sort_values("average_risk_score", ascending=False).round(3)
