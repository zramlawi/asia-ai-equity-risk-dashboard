"""Simple, transparent risk metrics for daily adjusted-close prices."""

import numpy as np
import pandas as pd


def daily_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Calculate simple daily returns from a wide price table."""
    if prices.empty:
        raise ValueError("Prices cannot be empty.")
    return prices.sort_index().pct_change(fill_method=None).dropna(how="all")


def annualized_volatility(returns: pd.DataFrame, trading_days: int = 252) -> pd.Series:
    """Calculate annualized sample volatility for each ticker."""
    if trading_days <= 0:
        raise ValueError("trading_days must be positive.")
    return returns.std(ddof=1) * np.sqrt(trading_days)


def maximum_drawdown(prices: pd.DataFrame) -> pd.Series:
    """Calculate maximum drawdown for each ticker as a negative decimal."""
    normalized = prices.sort_index().div(prices.sort_index().iloc[0])
    drawdown = normalized.div(normalized.cummax()).sub(1)
    return drawdown.min()


def risk_snapshot(prices: pd.DataFrame, volatility_threshold: float = 0.40) -> pd.DataFrame:
    """Build a compact, dashboard-ready table of core risk indicators."""
    returns = daily_returns(prices)
    snapshot = pd.DataFrame({
        "annualized_volatility": annualized_volatility(returns),
        "maximum_drawdown": maximum_drawdown(prices),
        "observations": prices.notna().sum(),
    })
    snapshot["risk_flag"] = np.where(
        snapshot["annualized_volatility"] >= volatility_threshold,
        "review",
        "normal",
    )
    return snapshot.sort_values("annualized_volatility", ascending=False)
