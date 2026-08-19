import os

import pandas as pd
import streamlit as st

from src.data import fetch_equity_data
from src.fundamentals import calculate_fundamentals, display_metrics
from src.macro import fetch_country_macro

st.set_page_config(page_title="Asia AI Equity Risk Dashboard", layout="wide")
st.title("Asia AI Equity Risk Dashboard")
st.caption("Free-data research dashboard. It is not investment advice.")

with st.sidebar:
    st.header("Inputs")
    symbol = st.text_input("Yahoo Finance ticker", value="TSM").strip().upper()
    country = st.text_input("World Bank country code", value="TWN").strip().upper()
    st.caption("Examples: TSM / TWN, 005930.KS / KOR, 7203.T / JPN")
    refresh = st.button("Refresh data")

@st.cache_data(ttl=900, show_spinner=False)
def load_equity(symbol_: str):
    return fetch_equity_data(symbol_)

@st.cache_data(ttl=3600, show_spinner=False)
def load_macro(country_: str):
    return fetch_country_macro(country_)

if refresh:
    load_equity.clear()
    load_macro.clear()

if not symbol:
    st.info("Enter a Yahoo Finance ticker to begin.")
    st.stop()

with st.spinner("Retrieving free public data..."):
    equity = load_equity(symbol)
    macro = load_macro(country) if country else None

prices = equity["prices"]
fundamental = calculate_fundamentals(equity["fundamentals"], prices)
tab_price, tab_fundamentals, tab_macro, tab_quality = st.tabs(["Price Risk", "Fundamentals & Liquidity", "Country Macro", "Data Quality"])

with tab_price:
    st.subheader(f"Price Risk — {symbol}")
    if prices.empty:
        st.warning("No price history was returned by Yahoo Finance for this ticker.")
    else:
        close = prices["Close"]
        rolling_high = close.cummax()
        drawdown = close / rolling_high - 1
        returns = close.pct_change().dropna()
        c1, c2, c3 = st.columns(3)
        c1.metric("Latest close", f"{close.iloc[-1]:,.2f}")
        c2.metric("Max drawdown", f"{drawdown.min():.1%}")
        c3.metric("Annualized volatility", f"{returns.std() * (252 ** 0.5):.1%}")
        st.line_chart(close, height=300)
        st.caption("Existing price-risk view is retained: chart, drawdown and annualized realised-volatility context from Yahoo Finance history.")

with tab_fundamentals:
    st.subheader(f"Fundamentals & Liquidity — {symbol}")
    a, b, c = st.columns(3)
    a.metric("Fundamental Stretch", "Not available" if fundamental["fundamental_stretch_score"] is None else f"{fundamental['fundamental_stretch_score']:.1f} / 100")
    b.metric("Liquidity Risk", "Not available" if fundamental["liquidity_risk_score"] is None else f"{fundamental['liquidity_risk_score']:.1f} / 100")
    c.metric("Field coverage", f"{fundamental['coverage']['percent']:.0f}%")
    st.caption(fundamental["score_note"])
    st.dataframe(display_metrics(fundamental), use_container_width=True, hide_index=True)
    missing = [name for name, state in equity["missing_status"].items() if state != "available"]
    if missing:
        st.info("Not reported by available free providers: " + ", ".join(missing))

with tab_macro:
    st.subheader(f"Country Macro — {country or 'No country selected'}")
    if not macro:
        st.info("Enter a World Bank country code to load macro context.")
    else:
        st.caption(macro["note"])
        macro_rows = []
        for name, item in macro["fields"].items():
            value = item["value"]
            macro_rows.append({"Indicator": name.replace("_", " ").title(), "Value": "No data" if value is None else f"{value:,.2f}", "Source date": item["source_date"] or "—", "Status": item["status"], "Detail": item["detail"]})
        st.metric("Macro coverage", f"{macro['coverage']['percent']:.0f}%")
        st.dataframe(pd.DataFrame(macro_rows), use_container_width=True, hide_index=True)

with tab_quality:
    st.subheader("Data Quality & Provider Status")
    st.write(f"Retrieved: {equity['retrieved_at']}")
    st.write("Sources: " + (", ".join(equity["sources"]) or "No provider returned data"))
    st.metric("Yahoo/Alpha fundamental coverage", f"{equity['coverage']['percent']:.0f}%")
    status_rows = []
    for name, item in equity["provider_status"].items():
        status_rows.append({"Provider": name, "Status": item["status"], "Source date": item["source_date"] or "—", "Checked": item["checked_at"], "Detail": item["detail"]})
    st.dataframe(pd.DataFrame(status_rows), use_container_width=True, hide_index=True)
    st.subheader("Provider-required modules")
    st.dataframe(pd.DataFrame([{"Module": k.replace("_", " ").title(), "Status": v} for k, v in equity["provider_required"].items()]), use_container_width=True, hide_index=True)
    if not os.getenv("ALPHA_VANTAGE_API_KEY"):
        st.info("Alpha Vantage enrichment is disabled. Add ALPHA_VANTAGE_API_KEY to a local environment or Streamlit secret to enable it; no key is needed for Yahoo Finance and World Bank data.")
