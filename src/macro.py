"""World Bank public country-macro client with explicit dates and failures."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests

WORLD_BANK = "https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
INDICATORS = {
    "gdp_growth_pct": "NY.GDP.MKTP.KD.ZG",
    "cpi_inflation_pct": "FP.CPI.TOTL.ZG",
    "unemployment_pct": "SL.UEM.TOTL.ZS",
    "current_account_pct_gdp": "BN.CAB.XOKA.GD.ZS",
    "official_exchange_rate": "PA.NUS.FCRF",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _latest(country: str, indicator: str) -> dict[str, Any]:
    checked_at = _now()
    try:
        response = requests.get(WORLD_BANK.format(country=country, indicator=indicator), params={"format": "json", "per_page": 20}, timeout=15)
        response.raise_for_status()
        payload = response.json()
        rows = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
        record = next((row for row in rows if row.get("value") is not None), None)
        if not record:
            return {"value": None, "source_date": None, "status": "no_data", "detail": "No non-null observation returned", "checked_at": checked_at}
        return {"value": record["value"], "source_date": record.get("date"), "status": "available", "detail": "", "checked_at": checked_at}
    except (requests.RequestException, ValueError, IndexError, TypeError) as exc:
        return {"value": None, "source_date": None, "status": "unavailable", "detail": str(exc), "checked_at": checked_at}


def fetch_country_macro(country_code: str) -> dict[str, Any]:
    country_code = country_code.strip().upper()
    fields = {name: _latest(country_code, indicator) for name, indicator in INDICATORS.items()}
    available = sum(item["status"] == "available" for item in fields.values())
    return {
        "country_code": country_code,
        "source": "World Bank Open Data",
        "retrieved_at": _now(),
        "fields": fields,
        "coverage": {"available_fields": available, "total_fields": len(INDICATORS), "percent": round(100 * available / len(INDICATORS), 1)},
        "note": "Values are latest available annual observations and may have different reference years.",
    }
