from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

import pandas as pd
import requests
import yfinance as yf

from .config import (
    DEFAULT_COUNTRY_CODE,
    MAX_YAHOO_AGE_HOURS,
    TICKER_COUNTRY_MAP,
    WORLD_BANK_BASE_URL,
)


@dataclass(frozen=True)
class FreshnessStatus:
    checked_at: datetime
    market_timestamp: datetime | None
    age_hours: float | None
    is_fresh: bool
    message: str


def ticker_to_country(ticker: str, override: str | None = None) -> str:
    """Map a ticker to a World Bank ISO-3 code, unless the user overrides it."""
    if override and override.strip():
        return override.strip().upper()

    normalized = ticker.strip().upper()
    if normalized in TICKER_COUNTRY_MAP:
        return TICKER_COUNTRY_MAP[normalized]

    suffix_map = {
        ".TW": "TWN", ".KS": "KOR", ".T": "JPN",
        ".HK": "CHN", ".SS": "CHN", ".SZ": "CHN",
        ".NS": "IND", ".BO": "IND",
    }
    return next((country for suffix, country in suffix_map.items() if normalized.endswith(suffix)), DEFAULT_COUNTRY_CODE)


def _to_utc_datetime(value: Any) -> datetime | None:
    if value is None or pd.isna(value):
        return None
    timestamp = pd.to_datetime(value, utc=True, errors="coerce")
    return None if pd.isna(timestamp) else timestamp.to_pydatetime()


def freshness_status(
    market_timestamp: Any,
    max_age_hours: int = MAX_YAHOO_AGE_HOURS,
    now: datetime | None = None,
) -> FreshnessStatus:
    """Return an explicit quote-age result; absent timestamps are not treated as fresh."""
    checked_at = now or datetime.now(timezone.utc)
    if checked_at.tzinfo is None:
        checked_at = checked_at.replace(tzinfo=timezone.utc)

    observed = _to_utc_datetime(market_timestamp)
    if observed is None:
        return FreshnessStatus(
            checked_at, None, None, False,
            "Yahoo Finance did not provide a usable market timestamp.",
        )

    age_hours = max(0.0, (checked_at - observed).total_seconds() / 3600)
    is_fresh = age_hours <= max_age_hours
    state = "fresh" if is_fresh else "stale"
    return FreshnessStatus(
        checked_at, observed, age_hours, is_fresh,
        f"Yahoo Finance quote is {state}: {age_hours:.1f} hours old.",
    )


def fetch_quote(
    ticker: str, max_age_hours: int = MAX_YAHOO_AGE_HOURS
) -> tuple[dict[str, Any], FreshnessStatus]:
    """Retrieve a provider quote without hiding provider failures or freshness uncertainty."""
    try:
        info = yf.Ticker(ticker).get_info() or {}
    except Exception as exc:
        info = {"provider_error": str(exc)}

    info["ticker"] = ticker
    status = freshness_status(
        info.get("regularMarketTime") or info.get("postMarketTime"),
        max_age_hours=max_age_hours,
    )
    info.update({
        "market_timestamp": status.market_timestamp,
        "quote_age_hours": status.age_hours,
        "is_fresh": status.is_fresh,
        "freshness_message": status.message,
    })
    return info, status


def fetch_quotes(
    tickers: Iterable[str], max_age_hours: int = MAX_YAHOO_AGE_HOURS
) -> pd.DataFrame:
    """Create a peer-ready table while retaining quote status and provider errors."""
    metric_keys = (
        "returnOnEquity", "operatingMargins", "profitMargins",
        "revenueGrowth", "currentRatio", "quickRatio", "debtToEquity",
    )
    rows: list[dict[str, Any]] = []
    for raw_ticker in tickers:
        ticker = raw_ticker.strip().upper()
        if not ticker:
            continue
        info, status = fetch_quote(ticker, max_age_hours)
        rows.append({
            "ticker": ticker,
            "name": info.get("shortName") or info.get("longName") or ticker,
            "price": info.get("regularMarketPrice"),
            "market_cap": info.get("marketCap"),
            "volume": info.get("regularMarketVolume"),
            "market_timestamp": status.market_timestamp,
            "quote_age_hours": status.age_hours,
            "is_fresh": status.is_fresh,
            "freshness_message": status.message,
            "provider_error": info.get("provider_error"),
            **{key: info.get(key) for key in metric_keys},
        })
    return pd.DataFrame(rows)


def _world_bank_payload(
    country: str, indicator: str, date: str, timeout: int = 20
) -> list[dict[str, Any]]:
    response = requests.get(
        f"{WORLD_BANK_BASE_URL}/country/{country}/indicator/{indicator}",
        params={"format": "json", "date": date, "per_page": 100},
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    return payload[1] if isinstance(payload, list) and len(payload) > 1 and payload[1] else []


def normalize_world_bank(
    records: list[dict[str, Any]], indicator_name: str
) -> pd.DataFrame:
    """Keep only reported observations and order annual World Bank data chronologically."""
    rows = [
        {
            "indicator": indicator_name,
            "year": int(record["date"]),
            "value": record.get("value"),
            "country": record.get("country", {}).get("value"),
            "country_code": record.get("countryiso3code"),
        }
        for record in records
        if record.get("date") and record.get("value") is not None
    ]
    columns = ["indicator", "year", "value", "country", "country_code"]
    return pd.DataFrame(rows, columns=columns).sort_values("year") if rows else pd.DataFrame(columns=columns)


def fetch_world_bank_history(
    country: str, indicator_name: str, indicator_code: str, years: int = 10
) -> pd.DataFrame:
    end_year = datetime.now(timezone.utc).year
    records = _world_bank_payload(
        country, indicator_code, f"{end_year - years + 1}:{end_year}"
    )
    return normalize_world_bank(records, indicator_name)


def fetch_world_bank_latest(
    country: str, indicators: dict[str, str]
) -> pd.DataFrame:
    """Return the latest published non-null value per requested macro indicator."""
    frames = []
    for name, code in indicators.items():
        history = fetch_world_bank_history(country, name, code, years=12)
        if not history.empty:
            frames.append(history.tail(1))
    columns = ["indicator", "year", "value", "country", "country_code"]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=columns)
