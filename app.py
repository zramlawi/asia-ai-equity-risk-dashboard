from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.analytics import (
    COMPANIES,
    MARKETS,
    load_price_frame,
    momentum_fundamentals,
    peer_comparison,
    performance_index,
    risk_return,
    speculation_signal,
)

st.set_page_config(page_title="Asia & U.S. Equity Risk Dashboard", layout="wide")
st.title("Asia & U.S. Equity Risk Dashboard")
st.caption("Market-aware price analytics with transparent speculation signals. Educational use only; not investment advice.")

with st.sidebar:
    st.header("Universe")
    region = st.selectbox("Region", list(MARKETS))
    market_names = st.multiselect("Market selectors", list(MARKETS[region]), default=list(MARKETS[region])[:2])
    company_names = st.multiselect("Curated company presets", list(COMPANIES[region]), default=list(COMPANIES[region])[:3])
    custom_tickers = st.text_input("Custom tickers (comma separated)", placeholder="e.g., TSM, NVDA, 7203.T")
    period = st.selectbox("History window", ["6mo", "1y", "2y", "5y"], index=1)

selected = [MARKETS[region][name] for name in market_names] + [COMPANIES[region][name] for name in company_names]
selected += [item.strip().upper() for item in custom_tickers.split(",") if item.strip()]
selected = list(dict.fromkeys(selected))

if not selected:
    st.info("Select at least one market, company preset, or custom ticker.")
    st.stop()

prices, source_results = load_price_frame(selected, period)
fallbacks = [f"{ticker}: {result.note}" for ticker, result in source_results.items() if result.source != "Yahoo Finance"]
if fallbacks:
    st.warning("Some Yahoo Finance inputs were unavailable. Deterministic synthetic price paths are shown for continuity and labeled below; do not treat them as market data.")
    with st.expander("Unavailable-input details"):
        st.write("\n".join(fallbacks))

price_source = pd.DataFrame({
    "Ticker": list(source_results),
    "Data source": [result.source for result in source_results.values()],
})
st.dataframe(price_source, hide_index=True, use_container_width=True)

perf = performance_index(prices)
fig_price = px.line(perf, x=perf.index, y=perf.columns, labels={"value": "Indexed price (start = 100)", "variable": "Ticker", "x": "Date"}, title="Price performance")
st.plotly_chart(fig_price, use_container_width=True)

metrics = risk_return(prices).reset_index(names="ticker")
fig_risk = px.scatter(metrics, x="annual_volatility", y="annual_return", text="ticker", title="Risk-return map", labels={"annual_volatility": "Annualized volatility", "annual_return": "Annualized return"})
fig_risk.update_traces(textposition="top center")
st.plotly_chart(fig_risk, use_container_width=True)

mf = momentum_fundamentals(prices, selected)
fig_mf = px.scatter(mf, x="fundamental_proxy", y="momentum_6m", text="ticker", color="momentum_3m", color_continuous_scale="RdYlGn", title="Momentum vs. fundamentals", labels={"fundamental_proxy": "Fundamental proxy (illustrative when live fundamentals are unavailable)", "momentum_6m": "Six-month momentum", "momentum_3m": "Three-month momentum"})
fig_mf.update_traces(textposition="top center")
st.plotly_chart(fig_mf, use_container_width=True)
st.caption("Fundamental proxy is intentionally disclosed as illustrative. It is not a Yahoo Finance-derived valuation or quality score.")

peers = peer_comparison(prices)
fig_peer = go.Figure(data=[go.Bar(name="Total return", x=peers["ticker"], y=peers["total_return"]), go.Bar(name="Annual volatility", x=peers["ticker"], y=peers["annual_volatility"])])
fig_peer.update_layout(barmode="group", title="Peer comparison", yaxis_tickformat=".0%")
st.plotly_chart(fig_peer, use_container_width=True)

st.subheader("Transparent speculation signal")
focus_ticker = st.selectbox("Ticker to explain", selected)
signal = speculation_signal(prices[focus_ticker].dropna())
a, b, c = st.columns(3)
a.metric("Signal score (0–100)", signal["score"])
b.metric("Label", signal["label"])
c.metric("Six-month momentum", f"{signal['momentum']:.1%}")
st.info(signal["explanation"])
st.markdown("**Method:** 45 points for six-month momentum, 35 for annualized trailing volatility, and 20 for maximum drawdown. Higher values indicate price behavior often associated with speculative conditions, not a forecast or a buy/sell recommendation.")

st.subheader("Peer metrics")
st.dataframe(peers.style.format({"annual_return": "{:.1%}", "annual_volatility": "{:.1%}", "total_return": "{:.1%}", "last_price": "{:.2f}"}), hide_index=True, use_container_width=True)
