"""Data-loading helpers for the dashboard."""

from pathlib import Path

import pandas as pd

from .config import REQUIRED_TICKER_COLUMNS, TICKERS_PATH


def load_tickers(path: str | Path = TICKERS_PATH) -> pd.DataFrame:
    """Load and validate the equity watchlist CSV."""
    tickers = pd.read_csv(path)
    missing = REQUIRED_TICKER_COLUMNS.difference(tickers.columns)
    if missing:
        raise ValueError(f"Ticker file is missing required columns: {sorted(missing)}")

    tickers["ticker"] = tickers["ticker"].astype(str).str.strip()
    if tickers["ticker"].eq("").any():
        raise ValueError("Ticker file contains blank ticker symbols.")

    return tickers.sort_values(["country", "company", "ticker"]).reset_index(drop=True)


def validate_watchlist(tickers: pd.DataFrame) -> pd.DataFrame:
    """Return rows that may require manual review before analysis."""
    duplicate_tickers = tickers[tickers.duplicated("ticker", keep=False)].copy()
    duplicate_tickers["review_reason"] = "duplicate ticker"

    company_counts = tickers.groupby("company")["ticker"].transform("count")
    multi_listed = tickers.loc[company_counts.gt(1)].copy()
    multi_listed["review_reason"] = "multiple listings; prevent double counting"

    review = pd.concat([duplicate_tickers, multi_listed], ignore_index=True)
    return review.drop_duplicates(subset=["ticker", "review_reason"]).reset_index(drop=True)
