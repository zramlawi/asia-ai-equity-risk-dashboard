"""Transparent normalisation and 0-100 fundamental and liquidity risk scoring."""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def number(value: Any) -> float | None:
    try:
        return None if value is None or pd.isna(value) else float(value)
    except (TypeError, ValueError):
        return None


def pct(value: Any) -> float | None:
    value = number(value)
    return None if value is None else 100 * value


def clamp(value: float, low: float = 0, high: float = 100) -> float:
    return round(max(low, min(high, value)), 1)


def _component(value: float | None, low: float, high: float, invert: bool = False) -> float | None:
    if value is None:
        return None
    scaled = 100 * (value - low) / (high - low)
    return clamp(100 - scaled if invert else scaled)


def _mean(values: list[float | None]) -> float | None:
    valid = [value for value in values if value is not None]
    return round(float(np.mean(valid)), 1) if valid else None


def calculate_fundamentals(raw: dict[str, Any], prices: pd.DataFrame | None = None) -> dict[str, Any]:
    pe, pb, ev_ebitda = number(raw.get("trailingPE")), number(raw.get("priceToBook")), number(raw.get("enterpriseToEbitda"))
    roe, margin, revenue_growth, earnings_growth = pct(raw.get("returnOnEquity")), pct(raw.get("profitMargins")), pct(raw.get("revenueGrowth")), pct(raw.get("earningsGrowth"))
    market_cap, avg_volume = number(raw.get("marketCap")), number(raw.get("averageVolume") or raw.get("averageDailyVolume10Day"))
    last_price = number(raw.get("lastPrice"))
    if last_price is None and prices is not None and not prices.empty:
        last_price = number(prices["Close"].iloc[-1])
    avg_dollar_volume = last_price * avg_volume if last_price is not None and avg_volume is not None else None
    debt, cash, current_ratio, quick_ratio = number(raw.get("totalDebt")), number(raw.get("totalCash")), number(raw.get("currentRatio")), number(raw.get("quickRatio"))
    net_debt = debt - cash if debt is not None and cash is not None else None
    stretch_parts = [_component(pe, 10, 50), _component(pb, 1, 10), _component(ev_ebitda, 5, 30), _component(roe, 5, 30, True), _component(margin, 2, 25, True), _component(revenue_growth, -10, 30, True), _component(earnings_growth, -20, 40, True)]
    liquidity_parts = [_component(avg_dollar_volume, 1_000_000, 100_000_000, True), _component(current_ratio, 0.5, 2.0, True), _component(quick_ratio, 0.3, 1.5, True)]
    available = {"pe": pe, "pb": pb, "ev_ebitda": ev_ebitda, "roe_pct": roe, "margin_pct": margin, "revenue_growth_pct": revenue_growth, "earnings_growth_pct": earnings_growth, "market_cap": market_cap, "average_daily_volume": avg_volume, "average_dollar_volume": avg_dollar_volume, "debt": debt, "cash": cash, "net_debt": net_debt, "current_ratio": current_ratio, "quick_ratio": quick_ratio}
    coverage = {"available_fields": sum(value is not None for value in available.values()), "total_fields": len(available), "percent": round(100 * sum(value is not None for value in available.values()) / len(available), 1)}
    return {"metrics": available, "coverage": coverage, "fundamental_stretch_score": _mean(stretch_parts), "liquidity_risk_score": _mean(liquidity_parts), "score_note": "Scores are 0-100 equal-weight averages of available components; higher denotes more stretch or liquidity risk. Missing fields are excluded, not imputed."}


def display_metrics(result: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for name, value in result["metrics"].items():
        label = name.replace("_", " ").title()
        if name.endswith("_pct") and value is not None:
            value = f"{value:.2f}%"
        elif isinstance(value, float):
            value = f"{value:,.2f}"
        rows.append({"Metric": label, "Value": "Not reported" if value is None else value})
    return pd.DataFrame(rows)
