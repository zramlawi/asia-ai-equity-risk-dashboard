"""Streamlit entry point for the Asia AI Equity Risk Dashboard."""

import pandas as pd
import streamlit as st
import yfinance as yf

from src.data import load_tickers, validate_watchlist
from src.risk import risk_snapshot


st.set_page_config(page_title="Asia AI Equity Risk Dashboard", layout="wide")


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_prices(symbols: tuple[str, ...], period: str) -> pd.DataFrame:
    """Download adjusted daily close prices for the selected symbols."""
    raw = yf.download(
        list(symbols),
        period=period,
        auto_adjust=True,
        progress=False,
        group_by="column",
    )
    if raw.empty:
        return pd.DataFrame()

    if isinstance(raw.columns, pd.MultiIndex):
        if "Close" not in raw.columns.get_level_values(0):
            return pd.DataFrame()
        prices = raw["Close"].copy()
    elif "Close" in raw.columns:
        prices = raw[["Close"]].copy()
        prices.columns = [symbols[0]]
    else:
        return pd.DataFrame()

    if isinstance(prices, pd.Series):
        prices = prices.to_frame(name=symbols[0])
    return prices.dropna(axis=1, how="all").dropna(how="all")


def format_risk_table(metrics: pd.DataFrame) -> pd.DataFrame:
    """Prepare metric labels for display without changing underlying calculations."""
    display = metrics.reset_index(names="ticker").copy()
    display["annualized_volatility"] = display["annualized_volatility"].map("{:.1%}".format)
    display["maximum_drawdown"] = display["maximum_drawdown"].map("{:.1%}".format)
    return display


def main() -> None:
    st.title("Asia AI Equity Risk Dashboard")
    st.caption("Example watchlist and historical market data only — not investment advice.")

    tickers = load_tickers()
    review_rows = validate_watchlist(tickers)

    st.sidebar.header("Controls")
    countries = sorted(tickers["country"].dropna().unique())
    selected_countries = st.sidebar.multiselect(
        "Countries",
        options=countries,
        default=countries,
    )
    period = st.sidebar.selectbox("Price history", ["6mo", "1y", "2y", "5y"], index=1)
    volatility_threshold = st.sidebar.slider(
        "Annualized-volatility review threshold",
        min_value=0.10,
        max_value=1.00,
        value=0.40,
        step=0.05,
        format="%.0f%%",
    )

    watchlist = tickers[tickers["country"].isin(selected_countries)].copy()
    st.subheader("Watchlist")
    st.dataframe(watchlist, use_container_width=True, hide_index=True)

    if watchlist.empty:
        st.info("Choose at least one country to load data.")
        return

    symbols = tuple(watchlist["ticker"].drop_duplicates().tolist())
    if st.button("Load market data", type="primary"):
        with st.spinner("Downloading historical adjusted-close prices..."):
            prices = fetch_prices(symbols, period)

        if prices.empty:
            st.error("No usable price data was returned. Check the ticker symbols, data-provider availability, and internet connection.")
            return

        metrics = risk_snapshot(prices, volatility_threshold=volatility_threshold)
        st.subheader("Risk snapshot")
        st.dataframe(format_risk_table(metrics), use_container_width=True, hide_index=True)

        st.subheader("Normalized price performance")
        normalized = prices.div(prices.iloc[0]).mul(100)
        st.line_chart(normalized)

        st.caption("Indexed to 100 at the first available observation for each security.")

    if not review_rows.empty:
        st.warning("Potential duplicate exposure: the watchlist includes multiple listings for some companies.")
        st.dataframe(review_rows, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
