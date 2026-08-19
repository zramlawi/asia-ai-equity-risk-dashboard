"""Price-derived market-risk indicators.

The score is a relative screen of price extension and realized risk; it is not a
bubble prediction, valuation model, or investment recommendation.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def _return_over(series: pd.Series, sessions: int) -> float:
    if len(series) <= sessions:
        return np.nan
    return (series.iloc[-1] / series.iloc[-(sessions + 1)] - 1.0) * 100


def _max_drawdown(series: pd.Series) -> float:
    running_high = series.cummax()
    return ((series / running_high) - 1.0).min() * 100


def calculate_price_metrics(prices: dict[str, pd.Series]) -> pd.DataFrame:
    """Calculate observables from each valid daily-close series."""
    records: list[dict[str, float | str | pd.Timestamp]] = []
    for ticker, raw_series in prices.items():
        series = raw_series.dropna().sort_index()
        if len(series) < 201:
            continue
        close = float(series.iloc[-1])
        ma50 = float(series.tail(50).mean())
        ma200 = float(series.tail(200).mean())
        trailing_high = float(series.max())
        daily_returns = series.pct_change().dropna()
        records.append(
            {
                "ticker": ticker,
                "data_date": series.index[-1].date(),
                "close": close,
                "return_3m": _return_over(series, 63),
                "return_6m": _return_over(series, 126),
                "return_12m": _return_over(series, 252),
                "distance_ma50": (close / ma50 - 1.0) * 100,
                "distance_ma200": (close / ma200 - 1.0) * 100,
                "distance_trailing_high": (close / trailing_high - 1.0) * 100,
                "annualized_volatility": daily_returns.std(ddof=1) * np.sqrt(TRADING_DAYS) * 100,
                "max_drawdown": _max_drawdown(series),
            }
        )
    return pd.DataFrame(records)


def _percentile(series: pd.Series) -> pd.Series:
    return series.rank(pct=True, method="average").fillna(0.5) * 100


def add_risk_score(metrics: pd.DataFrame) -> pd.DataFrame:
    """Add a transparent 0–100 relative price-risk score.

    Weights: 30% six-month momentum, 20% extension above the 200-day average,
    15% proximity to the trailing high, 20% realized volatility, and 15%
    drawdown severity. All components are percentiles within the loaded universe.
    """
    if metrics.empty:
        return metrics.copy()
    scored = metrics.copy()
    components = {
        "momentum_component": _percentile(scored["return_6m"]),
        "ma200_component": _percentile(scored["distance_ma200"]),
        "high_component": _percentile(scored["distance_trailing_high"]),
        "volatility_component": _percentile(scored["annualized_volatility"]),
        "drawdown_component": _percentile(-scored["max_drawdown"]),
    }
    for name, values in components.items():
        scored[name] = values
    scored["risk_score"] = (
        0.30 * scored["momentum_component"]
        + 0.20 * scored["ma200_component"]
        + 0.15 * scored["high_component"]
        + 0.20 * scored["volatility_component"]
        + 0.15 * scored["drawdown_component"]
    ).round(1)
    scored["risk_band"] = pd.cut(
        scored["risk_score"],
        bins=[-np.inf, 40, 70, np.inf],
        labels=["Lower", "Elevated", "High"],
    )
    return scored.sort_values("risk_score", ascending=False).reset_index(drop=True)
