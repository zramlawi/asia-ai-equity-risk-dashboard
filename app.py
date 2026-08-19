from pathlib import Path

import pandas as pd
import streamlit as st

from src.bubble import calculate_risk, country_summary


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "tickers.csv"

st.set_page_config(page_title="Asia AI Equity Risk Dashboard", page_icon="📊", layout="wide")


@st.cache_data
def load_universe(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"country", "ticker", "name"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"tickers.csv is missing required columns: {', '.join(sorted(missing))}")
    return df


def first_available(frame: pd.DataFrame, names: list[str]) -> str | None:
    return next((name for name in names if name in frame.columns), None)


def main() -> None:
    st.title("Asia AI Equity Risk Dashboard")
    st.caption("Scenario analysis of AI-related valuation and technology risk-off sensitivity. This is an educational dashboard, not investment advice.")

    try:
        universe = load_universe(DATA_PATH)
    except Exception as exc:
        st.error(f"Could not load {DATA_PATH.name}: {exc}")
        st.stop()

    country_col = first_available(universe, ["country", "Country"])
    ticker_col = first_available(universe, ["ticker", "Ticker", "symbol", "Symbol"])
    name_col = first_available(universe, ["name", "Name", "company", "Company"])

    if not all([country_col, ticker_col, name_col]):
        st.error("The input file must include country, ticker, and name columns.")
        st.stop()

    countries = sorted(universe[country_col].dropna().astype(str).unique())
    with st.sidebar:
        st.header("Scenario controls")
        selected_countries = st.multiselect("Countries", countries, default=countries)
        shock = st.slider("Global technology risk-off shock (%)", min_value=-40, max_value=0, value=-15, step=1) / 100
        valuation = st.slider("AI valuation compression (%)", min_value=0, max_value=50, value=20, step=1) / 100
        earnings = st.slider("AI earnings shortfall (%)", min_value=0, max_value=50, value=15, step=1) / 100
        st.caption("The engine combines disclosed input factors where available with transparent defaults.")

    if not selected_countries:
        st.info("Select at least one country to view results.")
        st.stop()

    filtered = universe[universe[country_col].astype(str).isin(selected_countries)].copy()
    scored = calculate_risk(filtered, market_shock=shock, valuation_compression=valuation, earnings_shortfall=earnings)
    summary = country_summary(scored)

    total = len(scored)
    high = int((scored["risk_band"] == "High").sum())
    average = scored["risk_score"].mean() if total else 0.0
    expected = scored["scenario_drawdown_pct"].mean() if total else 0.0

    a, b, c, d = st.columns(4)
    a.metric("Companies assessed", f"{total:,}")
    b.metric("Average risk score", f"{average:.1f}/100")
    c.metric("High-risk names", f"{high:,}")
    d.metric("Average scenario drawdown", f"{expected:.1%}")

    st.subheader("Country comparison")
    chart = summary.set_index("country")[["average_risk_score", "high_risk_share"]]
    st.bar_chart(chart)

    st.subheader("Company review table")
    display_columns = [
        col for col in ["country", "ticker", "name", "risk_score", "risk_band", "scenario_drawdown_pct", "valuation_risk", "earnings_risk", "market_risk"]
        if col in scored.columns
    ]
    st.dataframe(
        scored[display_columns].sort_values(["risk_score", "scenario_drawdown_pct"], ascending=[False, True]),
        use_container_width=True,
        hide_index=True,
        column_config={
            "risk_score": st.column_config.NumberColumn("Risk score", format="%.1f"),
            "scenario_drawdown_pct": st.column_config.NumberColumn("Scenario drawdown", format="%.1f%%"),
        },
    )

    st.subheader("Methodology")
    st.markdown("Risk scores are scenario-based and range from 0 to 100. Read `docs/bubble-risk-methodology.md` for factor definitions, default assumptions, and limitations.")


if __name__ == "__main__":
    main()
