from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

MARKETS = {
    "Asia Pacific": {
        "Japan (Nikkei 225)": "^N225",
        "Hong Kong (Hang Seng)": "^HSI",
        "China (Shanghai Composite)": "000001.SS",
        "South Korea (KOSPI)": "^KS11",
        "Taiwan (TAIEX)": "^TWII",
        "India (Nifty 50)": "^NSEI",
    },
    "United States": {
        "S&P 500": "^GSPC",
        "Nasdaq Composite": "^IXIC",
        "Dow Jones Industrial Average": "^DJI",
        "Russell 2000": "^RUT",
    },
}

COMPANIES = {
    "Asia Pacific": {
        "Taiwan Semiconductor": "TSM",
        "Samsung Electronics": "005930.KS",
        "Toyota Motor": "TM",
        "Sony Group": "SONY",
        "Tencent": "TCEHY",
        "Alibaba": "BABA",
        "Infosys": "INFY",
    },
    "United States": {
        "NVIDIA": "NVDA",
        "Microsoft": "MSFT",
        "Apple": "AAPL",
        "Amazon": "AMZN",
        "Alphabet": "GOOGL",
        "Meta Platforms": "META",
        "Tesla": "TSLA",
    },
}


@dataclass(frozen=True)
class PriceResult:
    prices: pd.Series
    source: str
    note: str = ""


def normalize_tickers(tickers: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(t.strip().upper() for t in tickers if t and t.strip()))


def available_tickers(region: str, include_markets: bool = True) -> dict[str, str]:
    universe = dict(COMPANIES.get(region, {}))
    if include_markets:
        universe = {**MARKETS.get(region, {}), **universe}
    return universe


def synthetic_prices(ticker: str, periods: int = 252) -> pd.Series:
    seed = sum(ord(char) for char in ticker) % (2**32 - 1)
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=periods)
    drift = ((seed % 17) - 8) / 20000
    volatility = 0.012 + (seed % 8) / 4000
    returns = rng.normal(drift, volatility, periods)
    prices = 100 * np.exp(np.cumsum(returns))
    return pd.Series(prices, index=dates, name=ticker)


def load_prices(ticker: str, period: str = "1y") -> PriceResult:
    ticker = ticker.upper().strip()
    try:
        import yfinance as yf

        frame = yf.download(ticker, period=period, auto_adjust=True, progress=False, threads=False)
        if isinstance(frame, pd.DataFrame) and not frame.empty:
            close = frame["Close"]
            if isinstance(close, pd.DataFrame):
                close = close.iloc[:, 0]
            close = pd.Series(close).dropna()
            if len(close) >= 20:
                close.name = ticker
                return PriceResult(close, "Yahoo Finance")
        raise ValueError("No usable closing-price history returned")
    except Exception as exc:
        return PriceResult(synthetic_prices(ticker), "Deterministic fallback", f"Yahoo Finance unavailable: {exc}")


def load_price_frame(tickers: Iterable[str], period: str = "1y") -> tuple[pd.DataFrame, dict[str, PriceResult]]:
    results = {ticker: load_prices(ticker, period) for ticker in normalize_tickers(tickers)}
    frame = pd.concat({ticker: result.prices for ticker, result in results.items()}, axis=1).sort_index().ffill().dropna(how="all")
    return frame, results


def performance_index(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.divide(prices.iloc[0]).multiply(100)


def risk_return(prices: pd.DataFrame) -> pd.DataFrame:
    daily = prices.pct_change().dropna(how="all")
    annual_return = (1 + daily.mean()) ** 252 - 1
    annual_volatility = daily.std() * np.sqrt(252)
    return pd.DataFrame({"annual_return": annual_return, "annual_volatility": annual_volatility})


def momentum_fundamentals(prices: pd.DataFrame, tickers: Iterable[str]) -> pd.DataFrame:
    latest = prices.ffill().iloc[-1]
    momentum_3m = prices.pct_change(63).iloc[-1]
    momentum_6m = prices.pct_change(126).iloc[-1]
    rows = []
    for ticker in normalize_tickers(tickers):
        seed = sum(map(ord, ticker))
        rows.append({
            "ticker": ticker,
            "last_price": float(latest.get(ticker, np.nan)),
            "momentum_3m": float(momentum_3m.get(ticker, np.nan)),
            "momentum_6m": float(momentum_6m.get(ticker, np.nan)),
            "fundamental_proxy": 35 + seed % 60,
            "fundamental_label": "Unavailable from Yahoo Finance; proxy is illustrative",
        })
    return pd.DataFrame(rows)


def speculation_signal(prices: pd.Series) -> dict[str, float | str]:
    daily = prices.pct_change().dropna()
    momentum = float(prices.iloc[-1] / prices.iloc[max(0, len(prices) - 63)] - 1) if len(prices) >= 2 else 0.0
    volatility = float(daily.tail(63).std() * np.sqrt(252)) if len(daily) else 0.0
    drawdown = float((prices / prices.cummax() - 1).min()) if len(prices) else 0.0
    momentum_points = float(np.clip(momentum / 0.60, 0, 1) * 45)
    volatility_points = float(np.clip(volatility / 0.80, 0, 1) * 35)
    drawdown_points = float(np.clip(abs(drawdown) / 0.35, 0, 1) * 20)
    score = round(momentum_points + volatility_points + drawdown_points, 1)
    label = "High speculation signal" if score >= 67 else "Moderate speculation signal" if score >= 34 else "Lower speculation signal"
    explanation = (
        f"Score = momentum ({momentum_points:.1f}/45) + volatility ({volatility_points:.1f}/35) + "
        f"drawdown ({drawdown_points:.1f}/20). This is a transparent market-behavior indicator, not investment advice."
    )
    return {
        "score": score, "label": label, "momentum": momentum, "volatility": volatility,
        "max_drawdown": drawdown, "explanation": explanation,
    }


def peer_comparison(prices: pd.DataFrame) -> pd.DataFrame:
    metrics = risk_return(prices)
    latest = prices.ffill().iloc[-1]
    total_return = prices.iloc[-1] / prices.iloc[0] - 1
    metrics["total_return"] = total_return
    metrics["last_price"] = latest
    return metrics.reset_index(names="ticker")
