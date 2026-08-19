"""Live Yahoo Finance price retrieval and data-quality reporting."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd
import yfinance as yf

DEFAULT_PERIOD = "2y"
REQUIRED_HISTORY_DAYS = 210


@dataclass
class MarketDataResult:
    prices: dict[str, pd.Series]
    failures: pd.DataFrame
    updated_at: datetime


def load_watchlist(path: str | Path = "data/tickers.csv") -> pd.DataFrame:
    """Load and validate the dashboard watchlist."""
    watchlist = pd.read_csv(path, dtype=str).fillna("")
    required = {"company", "ticker", "country", "exchange", "theme"}
    missing = required.difference(watchlist.columns)
    if missing:
        raise ValueError(f"Watchlist is missing columns: {', '.join(sorted(missing))}")
    watchlist["ticker"] = watchlist["ticker"].str.strip()
    return watchlist.drop_duplicates(subset="ticker").reset_index(drop=True)


def _close_series(frame: pd.DataFrame, ticker: str) -> pd.Series:
    if frame.empty:
        return pd.Series(dtype=float)
    if isinstance(frame.columns, pd.MultiIndex):
        if ("Close", ticker) in frame.columns:
            series = frame[("Close", ticker)]
        elif ("Adj Close", ticker) in frame.columns:
            series = frame[("Adj Close", ticker)]
        else:
            return pd.Series(dtype=float)
    else:
        column = "Close" if "Close" in frame.columns else "Adj Close"
        series = frame[column] if column in frame.columns else pd.Series(dtype=float)
    return pd.to_numeric(series, errors="coerce").dropna().rename(ticker)


def download_prices(tickers: Iterable[str], period: str = DEFAULT_PERIOD) -> MarketDataResult:
    """Download daily close prices and record every unavailable or insufficient ticker."""
    ticker_list = list(dict.fromkeys(str(t).strip() for t in tickers if str(t).strip()))
    if not ticker_list:
        return MarketDataResult({}, pd.DataFrame(columns=["ticker", "reason"]), datetime.now(timezone.utc))

    try:
        raw = yf.download(
            tickers=ticker_list,
            period=period,
            interval="1d",
            auto_adjust=True,
            progress=False,
            group_by="column",
            threads=True,
        )
    except Exception as exc:
        failures = pd.DataFrame({"ticker": ticker_list, "reason": [f"download error: {exc}"] * len(ticker_list)})
        return MarketDataResult({}, failures, datetime.now(timezone.utc))

    prices: dict[str, pd.Series] = {}
    failures: list[dict[str, str]] = []
    for ticker in ticker_list:
        series = _close_series(raw, ticker)
        if series.empty:
            failures.append({"ticker": ticker, "reason": "No daily close prices returned by Yahoo Finance"})
        elif len(series) < REQUIRED_HISTORY_DAYS:
            failures.append({"ticker": ticker, "reason": f"Only {len(series)} observations; need at least {REQUIRED_HISTORY_DAYS}"})
        else:
            prices[ticker] = series

    return MarketDataResult(
        prices=prices,
        failures=pd.DataFrame(failures, columns=["ticker", "reason"]),
        updated_at=datetime.now(timezone.utc),
    )
