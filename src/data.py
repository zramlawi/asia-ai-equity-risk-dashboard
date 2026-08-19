"""Free public-market data retrieval with explicit provenance and coverage."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import requests
import yfinance as yf


FUNDAMENTAL_FIELDS = [
    "marketCap", "trailingPE", "forwardPE", "priceToBook", "enterpriseToEbitda",
    "trailingEps", "returnOnEquity", "profitMargins", "revenueGrowth",
    "earningsGrowth", "totalCash", "totalDebt", "currentRatio", "quickRatio",
    "operatingCashflow", "freeCashflow", "sharesOutstanding", "averageVolume",
    "averageDailyVolume10Day", "fiftyTwoWeekHigh", "fiftyTwoWeekLow",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _status(provider: str, state: str, detail: str = "", source_date: str | None = None) -> dict[str, str]:
    return {"provider": provider, "status": state, "detail": detail, "checked_at": utc_now(), "source_date": source_date or ""}


def alpha_vantage_key() -> str | None:
    return os.getenv("ALPHA_VANTAGE_API_KEY") or os.getenv("alpha_vantage_api_key")


def _read_yahoo_info(ticker: yf.Ticker) -> tuple[dict[str, Any], str]:
    try:
        info = ticker.get_info() or {}
        return info, "available"
    except Exception as exc:
        return {}, f"unavailable: {exc}"


def _alpha_vantage_overview(symbol: str, key: str) -> tuple[dict[str, Any], str]:
    try:
        response = requests.get(
            "https://www.alphavantage.co/query",
            params={"function": "OVERVIEW", "symbol": symbol, "apikey": key},
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        if "Note" in payload or "Information" in payload:
            return {}, payload.get("Note") or payload.get("Information")
        return payload if payload.get("Symbol") else {}, "available" if payload.get("Symbol") else "no record returned"
    except requests.RequestException as exc:
        return {}, f"unavailable: {exc}"


def _coerce(value: Any) -> float | None:
    if value in (None, "", "None", "-", "N/A"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fetch_equity_data(symbol: str, period: str = "2y") -> dict[str, Any]:
    """Return prices, free fundamentals, provider status, and missing-field reporting."""
    symbol = symbol.strip().upper()
    report: dict[str, Any] = {
        "symbol": symbol,
        "retrieved_at": utc_now(),
        "sources": [],
        "provider_status": {},
        "missing_status": {},
        "prices": pd.DataFrame(),
        "fundamentals": {},
        "coverage": {},
    }
    try:
        ticker = yf.Ticker(symbol)
        prices = ticker.history(period=period, auto_adjust=True)
        if prices.empty:
            report["provider_status"]["Yahoo Finance prices"] = _status("Yahoo Finance", "no_data", "No price history returned")
        else:
            prices.index = pd.to_datetime(prices.index).tz_localize(None)
            report["prices"] = prices
            report["provider_status"]["Yahoo Finance prices"] = _status(
                "Yahoo Finance", "available", source_date=str(prices.index.max().date())
            )
            report["sources"].append("Yahoo Finance (price history)")
        yahoo, yahoo_status = _read_yahoo_info(ticker)
        report["provider_status"]["Yahoo Finance fundamentals"] = _status("Yahoo Finance", "available" if yahoo else "partial", yahoo_status)
        report["sources"].append("Yahoo Finance (quote summary)")
    except Exception as exc:
        yahoo = {}
        report["provider_status"]["Yahoo Finance prices"] = _status("Yahoo Finance", "unavailable", str(exc))
        report["provider_status"]["Yahoo Finance fundamentals"] = _status("Yahoo Finance", "unavailable", str(exc))

    fundamentals = {field: yahoo.get(field) for field in FUNDAMENTAL_FIELDS}
    fundamentals["currency"] = yahoo.get("currency")
    fundamentals["longName"] = yahoo.get("longName") or yahoo.get("shortName")
    fundamentals["sector"] = yahoo.get("sector")
    fundamentals["quoteType"] = yahoo.get("quoteType")
    fundamentals["lastPrice"] = yahoo.get("regularMarketPrice")

    key = alpha_vantage_key()
    if key:
        alpha, alpha_status = _alpha_vantage_overview(symbol, key)
        report["provider_status"]["Alpha Vantage"] = _status("Alpha Vantage", "available" if alpha else "partial", alpha_status)
        if alpha:
            report["sources"].append("Alpha Vantage (optional OVERVIEW)")
            av_map = {"PERatio": "trailingPE", "PriceToBookRatio": "priceToBook", "EVToEBITDA": "enterpriseToEbitda", "EPS": "trailingEps", "ProfitMargin": "profitMargins", "ReturnOnEquityTTM": "returnOnEquity", "RevenueTTM": "revenueTTM", "EBITDA": "ebitda"}
            for av_name, local_name in av_map.items():
                if fundamentals.get(local_name) in (None, ""):
                    fundamentals[local_name] = _coerce(alpha.get(av_name))
    else:
        report["provider_status"]["Alpha Vantage"] = _status("Alpha Vantage", "disabled", "Set ALPHA_VANTAGE_API_KEY locally to enable optional enrichment")

    for field in FUNDAMENTAL_FIELDS:
        if fundamentals.get(field) in (None, ""):
            report["missing_status"][field] = "not reported by available providers"
        else:
            report["missing_status"][field] = "available"
    available = sum(value == "available" for value in report["missing_status"].values())
    report["coverage"] = {"available_fields": available, "total_fields": len(FUNDAMENTAL_FIELDS), "percent": round(100 * available / len(FUNDAMENTAL_FIELDS), 1)}
    report["fundamentals"] = fundamentals
    report["provider_required"] = {
        "analyst_estimates": "Unavailable: provider-required",
        "options": "Unavailable: provider-required",
        "short_interest": "Unavailable: provider-required",
        "institutional_ownership": "Unavailable: provider-required",
        "live_geopolitical_events": "Unavailable: provider-required",
    }
    return report
