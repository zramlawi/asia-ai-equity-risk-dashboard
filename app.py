from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.analytics import COMPANIES, MARKETS, load_price_frame, performance_index, price_features, risk_return
from src.bubble import peer_comparison_chart
from src.data import fetch_quotes
from src.risk import contribution_frame, historical_percentile, score_peer_frame

st.set_page_config(page_title="Asia & U.S. Equity Risk Dashboard", layout="wide")
st.title("Asia & U.S. Equity Risk Dashboard")
st.caption("Five-pillar, evidence-aware scenario analysis. Educational use only; not investment advice.")

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
fallbacks = [ticker for ticker, result in source_results.items() if not result.scoring_eligible]
if fallbacks:
    st.warning("Fallback price paths are shown only for chart continuity. They are excluded from all multi-signal scoring.")

status_rows = []
for ticker, result in source_results.items():
    status_rows.append({
        "ticker": ticker,
        "price_source": result.source,
        "price_status": "live" if result.scoring_eligible else "fallback",
        "price_scoring_eligible": result.scoring_eligible,
        "note": result.note,
    })
st.subheader("Data status")
st.dataframe(pd.DataFrame(status_rows), hide_index=True, use_container_width=True)

perf = performance_index(prices)
st.plotly_chart(px.line(perf, x=perf.index, y=perf.columns, title="Price performance", labels={"value": "Indexed price (start = 100)", "variable": "Ticker", "x": "Date"}), use_container_width=True)

metrics = risk_return(prices).reset_index(names="ticker")
fig_risk = px.scatter(metrics, x="annual_volatility", y="annual_return", text="ticker", title="Risk-return map")
fig_risk.update_traces(textposition="top center")
st.plotly_chart(fig_risk, use_container_width=True)

quotes = fetch_quotes(selected)
features = []
for ticker in selected:
    feature = price_features(prices[ticker], source_results[ticker].scoring_eligible)
    feature["ticker"] = ticker
    features.append(feature)
feature_frame = pd.DataFrame(features)
peer_input = quotes.merge(feature_frame, on="ticker", how="left")
for column in ["momentum_3m", "momentum_6m", "annual_volatility", "max_drawdown"]:
    peer_input[f"{column}_eligible"] = peer_input["price_scoring_eligible"].fillna(False)
peer_input["relative_volume"] = peer_input["volume"] / peer_input["average_volume"]
peer_input["relative_volume_eligible"] = peer_input["volume_eligible"].fillna(False) & peer_input["averageVolume_eligible"].fillna(False)
peer_input["volume_growth"] = np.nan
peer_input["volume_growth_eligible"] = False

peers = score_peer_frame(peer_input)
for ticker in peers["ticker"]:
    values = peers.loc[peers["ticker"] == ticker, "overall_score"]
    peers.loc[peers["ticker"] == ticker, "historical_percentile"] = historical_percentile(values.iloc[0], peers["overall_score"])

st.subheader("Core multi-signal score")
st.caption("Scores use only fresh, live Yahoo Finance evidence. Missing, stale, and fallback values reduce coverage instead of being imputed.")
score_columns = [
    "ticker", "overall_score", "coverage", "percentile", "historical_percentile",
    "price_score", "valuation_score", "fundamentals_score", "activity_volume_score",
    "fragility_score", "regime_points", "regime_rules", "scoring_eligible",
]
st.dataframe(peers.reindex(columns=score_columns).style.format({
    "overall_score": "{:.1f}", "coverage": "{:.0%}", "percentile": "{:.0f}",
    "historical_percentile": "{:.0f}", "price_score": "{:.1f}", "valuation_score": "{:.1f}",
    "fundamentals_score": "{:.1f}", "activity_volume_score": "{:.1f}", "fragility_score": "{:.1f}",
}), hide_index=True, use_container_width=True)

if not peers.empty and peers["valuation_score"].notna().any() and peers["fundamentals_score"].notna().any():
    st.plotly_chart(peer_comparison_chart(peers), use_container_width=True)

focus_ticker = st.selectbox("Ticker to explain", selected)
focus_row = peers.loc[peers["ticker"] == focus_ticker].iloc[0].to_dict()
focus_score = {key: focus_row.get(key) for key in focus_row}
focus_score["contributions"] = {
    pillar: focus_row.get(f"{pillar}_score") * 0 if pd.isna(focus_row.get(f"{pillar}_score")) else None
    for pillar in []
}
from src.risk import score_company
raw_focus = peer_input.loc[peer_input["ticker"] == focus_ticker].iloc[0].to_dict()
calculated = score_company(raw_focus)
a, b, c, d = st.columns(4)
a.metric("Risk score", "Unavailable" if calculated["overall_score"] is None else f"{calculated['overall_score']:.1f}")
b.metric("Live evidence coverage", f"{calculated['coverage']:.0%}")
c.metric("Peer percentile", "Unavailable" if pd.isna(focus_row.get("percentile")) else f"{focus_row['percentile']:.0f}")
d.metric("Regime adjustment", f"+{calculated['regime_points']:.0f}")

contributions = contribution_frame(calculated).dropna()
if not contributions.empty:
    st.plotly_chart(px.bar(contributions, x="pillar", y="contribution", title="Weighted pillar contributions", labels={"pillar": "Pillar", "contribution": "Contribution to base score"}), use_container_width=True)

st.subheader("Method and limits")
st.markdown(
    "Five pillars are price, valuation, fundamentals, activity/volume, and fragility. "
    "Pillar weights are coverage-adjusted: only fields with fresh live Yahoo Finance evidence contribute. "
    "Regime rules add documented risk points when annualized volatility exceeds 45% or drawdown exceeds 30%. "
    "Yahoo Finance coverage can be delayed or incomplete; this dashboard is not investment advice."
)
