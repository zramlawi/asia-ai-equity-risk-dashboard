from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from src.bubble import peer_comparison_chart
from src.config import WORLD_BANK_INDICATORS
from src.data import (
    fetch_quotes,
    fetch_world_bank_history,
    fetch_world_bank_latest,
    ticker_to_country,
)
from src.risk import score_company, score_peer_frame


st.set_page_config(page_title="Asia AI Equity Risk Dashboard", layout="wide")
st.title("Asia AI Equity Risk Dashboard")
st.caption(
    "A transparent research tool. Market and macro data may be delayed, incomplete, "
    "or revised; this is not investment advice."
)


def parse_tickers(value: str) -> list[str]:
    return [item.strip().upper() for item in value.split(",") if item.strip()]


def metric_text(value: object, digits: int = 1) -> str:
    return f"{float(value):.{digits}f}" if pd.notna(value) else "N/A"


primary_ticker = st.sidebar.text_input("Primary ticker", value="TSM").strip().upper()
peer_input = st.sidebar.text_input(
    "Optional peer tickers (comma-separated)",
    value="005930.KS, 9984.T, 0700.HK",
)
auto_country = ticker_to_country(primary_ticker)
country_code = st.sidebar.text_input(
    "World Bank country code (editable)",
    value=auto_country,
    help="Use an ISO-3 code. The automatic ticker mapping can be overridden.",
).strip().upper()
minimum_coverage = st.sidebar.slider(
    "Minimum score coverage for peer percentile",
    min_value=0.0,
    max_value=1.0,
    value=0.50,
    step=0.05,
)

peer_tickers = parse_tickers(peer_input)
tickers = list(dict.fromkeys([primary_ticker, *peer_tickers]))

if st.button("Refresh data", type="primary"):
    with st.spinner("Retrieving Yahoo Finance quotes and World Bank indicators…"):
        quotes = fetch_quotes(tickers)
        scores = score_peer_frame(quotes, minimum_coverage=minimum_coverage)

        macro_error = None
        try:
            latest_macro = fetch_world_bank_latest(country_code, WORLD_BANK_INDICATORS)
            histories = [
                fetch_world_bank_history(country_code, name, code)
                for name, code in WORLD_BANK_INDICATORS.items()
            ]
            macro_history = (
                pd.concat(histories, ignore_index=True)
                if histories
                else pd.DataFrame()
            )
        except Exception as exc:
            latest_macro = pd.DataFrame(
                columns=["indicator", "year", "value", "country", "country_code"]
            )
            macro_history = pd.DataFrame()
            macro_error = str(exc)

        st.session_state.update(
            {
                "scores": scores,
                "latest_macro": latest_macro,
                "macro_history": macro_history,
                "country_code": country_code,
                "macro_error": macro_error,
            }
        )

if "scores" not in st.session_state:
    st.info("Set the tickers and click Refresh data.")
    st.stop()

scores = st.session_state["scores"]
primary_rows = scores.loc[scores["ticker"] == primary_ticker]

if not primary_rows.empty:
    primary = primary_rows.iloc[0]
    st.subheader(f"{primary_ticker}: data quality and transparent score")

    if primary.get("provider_error"):
        st.error(f"Yahoo Finance error: {primary['provider_error']}")
    elif primary.get("is_fresh"):
        st.success(primary.get("freshness_message", "Fresh Yahoo Finance quote."))
    else:
        st.warning(primary.get("freshness_message", "Yahoo Finance freshness unavailable."))

    left, center_left, center_right, right = st.columns(4)
    left.metric("Fundamental score", metric_text(primary.get("fundamental_score")))
    center_left.metric("Liquidity score", metric_text(primary.get("liquidity_score")))
    center_right.metric("Evidence coverage", f"{primary.get('coverage', 0):.0%}")
    right.metric(
        "Peer percentile",
        metric_text(primary.get("percentile"), digits=0)
        if pd.notna(primary.get("percentile"))
        else "Insufficient coverage",
    )

    with st.expander("Scoring methodology and components"):
        st.write(
            "Fundamental score uses return on equity, operating margin, profit margin, "
            "and revenue growth. Liquidity score uses current ratio, quick ratio, and "
            "debt-to-equity. Missing fields lower evidence coverage rather than being imputed."
        )
        st.json(score_company(primary.to_dict()))

st.subheader("Peer comparison")
peer_columns = [
    "ticker", "name", "price", "quote_age_hours", "is_fresh",
    "fundamental_score", "liquidity_score", "overall_score",
    "coverage", "percentile",
]
st.dataframe(scores.reindex(columns=peer_columns), use_container_width=True)
if len(scores) > 1 and scores["overall_score"].notna().any():
    st.plotly_chart(peer_comparison_chart(scores), use_container_width=True)

st.subheader(f"World Bank macroeconomic context: {st.session_state['country_code']}")
if st.session_state.get("macro_error"):
    st.warning(f"World Bank data could not be retrieved: {st.session_state['macro_error']}")

latest_macro = st.session_state["latest_macro"]
if latest_macro.empty:
    st.info("No World Bank observations were returned for the selected country code.")
else:
    st.dataframe(
        latest_macro[["indicator", "year", "value"]],
        use_container_width=True,
    )

macro_history = st.session_state["macro_history"]
if not macro_history.empty:
    macro_chart = macro_history.pivot(
        index="year", columns="indicator", values="value"
    ).sort_index()
    st.line_chart(macro_chart)

st.subheader("CSV research snapshot")
macro_snapshot = latest_macro[["indicator", "year", "value"]]
snapshot = (
    scores.merge(macro_snapshot, how="cross")
    if not macro_snapshot.empty
    else scores.copy()
)
st.download_button(
    "Download CSV snapshot",
    data=snapshot.to_csv(index=False).encode("utf-8"),
    file_name=f"{primary_ticker.lower()}_risk_snapshot.csv",
    mime="text/csv",
)

with st.expander("Raw snapshot preview"):
    st.code(json.dumps(snapshot.head(20).to_dict(orient="records"), default=str, indent=2))
