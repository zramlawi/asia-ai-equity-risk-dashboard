from __future__ import annotations

from datetime import timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from src.bubble import add_risk_score, calculate_price_metrics
from src.data import download_prices, load_watchlist

st.set_page_config(page_title="Asia AI Equity Price-Risk Dashboard", layout="wide")


@st.cache_data(ttl=timedelta(minutes=30), show_spinner=False)
def refresh_market_data() -> tuple[pd.DataFrame, pd.DataFrame, str]:
    watchlist = load_watchlist()
    result = download_prices(watchlist["ticker"])
    metrics = add_risk_score(calculate_price_metrics(result.prices))
    successful = watchlist.merge(metrics, on="ticker", how="inner")
    failed = watchlist.merge(result.failures, on="ticker", how="inner")
    return successful, failed, result.updated_at.strftime("%Y-%m-%d %H:%M UTC")


st.title("Asia AI Equity Price-Risk Dashboard")
st.caption("A market-data research screen using Yahoo Finance daily prices. It measures relative price extension and realized risk; it does not predict bubbles or provide investment advice.")

if st.button("Refresh market data", type="primary"):
    st.cache_data.clear()

with st.spinner("Downloading daily market data from Yahoo Finance..."):
    results, failed_downloads, updated_at = refresh_market_data()

st.caption(f"Last market-data update: {updated_at}")

countries = ["All covered markets"] + sorted(results["country"].unique().tolist()) if not results.empty else ["All covered markets"]
selected_country = st.selectbox("Country / market", countries)
filtered = results if selected_country == "All covered markets" else results[results["country"] == selected_country]

average_score = filtered["risk_score"].mean() if not filtered.empty else float("nan")
high_risk = int((filtered["risk_band"] == "High").sum()) if not filtered.empty else 0
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Watchlist names", len(load_watchlist()))
c2.metric("Successful downloads", len(results))
c3.metric("Failed downloads", len(failed_downloads))
c4.metric("Average risk score", f"{average_score:.1f}" if pd.notna(average_score) else "—")
c5.metric("High-risk names", high_risk)

if filtered.empty:
    st.warning("No valid prices were loaded for this selection. Review the failed-download table below and try refresh.")
else:
    country_summary = results.groupby("country", as_index=False).agg(
        average_risk_score=("risk_score", "mean"),
        high_risk_share=("risk_band", lambda x: (x == "High").mean() * 100),
        names=("ticker", "count"),
    )
    chart_left, chart_right = st.columns(2)
    with chart_left:
        st.plotly_chart(
            px.bar(country_summary, x="country", y="average_risk_score", color="average_risk_score", range_color=[0, 100], title="Average price-risk score by market"),
            use_container_width=True,
        )
    with chart_right:
        st.plotly_chart(
            px.bar(country_summary, x="country", y="high_risk_share", color="high_risk_share", range_color=[0, 100], title="High-risk share by market (%)"),
            use_container_width=True,
        )

    st.subheader("Price-risk screen")
    columns = [
        "ticker", "company", "country", "theme", "risk_score", "risk_band", "return_3m", "return_6m", "return_12m",
        "distance_ma50", "distance_ma200", "distance_trailing_high", "annualized_volatility", "max_drawdown", "close", "data_date",
    ]
    table = filtered[columns].copy().sort_values("risk_score", ascending=False)
    numeric_columns = [c for c in columns if c not in {"ticker", "company", "country", "theme", "risk_band", "data_date"}]
    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
        column_config={column: st.column_config.NumberColumn(format="%.1f") for column in numeric_columns},
    )

st.subheader("Failed downloads")
if failed_downloads.empty:
    st.success("Every watchlist ticker returned enough daily price history for the current calculation window.")
else:
    st.dataframe(failed_downloads[["ticker", "company", "country", "exchange", "reason"]], use_container_width=True, hide_index=True)
    st.caption("Failures are shown explicitly rather than being replaced with simulated values. Yahoo Finance symbols, availability, and history can change.")

with st.expander("How the score works"):
    st.markdown("""
The 0–100 score ranks only the securities that returned valid data in the current refresh. It combines six-month momentum (30%), distance above the 200-day moving average (20%), proximity to the trailing high (15%), annualized historical volatility (20%), and maximum-drawdown severity (15%). A high score indicates relative price extension and realized risk within this selected universe—not a forecast of a bubble or a trading signal.
""")
