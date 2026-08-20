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


COUNTRY_OPTIONS = {
    "Afghanistan": "AFG", "Albania": "ALB", "Algeria": "DZA", "American Samoa": "ASM", "Andorra": "AND",
    "Angola": "AGO", "Antigua and Barbuda": "ATG", "Argentina": "ARG", "Armenia": "ARM", "Aruba": "ABW",
    "Australia": "AUS", "Austria": "AUT", "Azerbaijan": "AZE", "Bahamas": "BHS", "Bahrain": "BHR",
    "Bangladesh": "BGD", "Barbados": "BRB", "Belarus": "BLR", "Belgium": "BEL", "Belize": "BLZ",
    "Benin": "BEN", "Bermuda": "BMU", "Bhutan": "BTN", "Bolivia": "BOL", "Bosnia and Herzegovina": "BIH",
    "Botswana": "BWA", "Brazil": "BRA", "Brunei Darussalam": "BRN", "Bulgaria": "BGR", "Burkina Faso": "BFA",
    "Burundi": "BDI", "Cabo Verde": "CPV", "Cambodia": "KHM", "Cameroon": "CMR", "Canada": "CAN",
    "Cayman Islands": "CYM", "Central African Republic": "CAF", "Chad": "TCD", "Chile": "CHL",
    "China": "CHN", "Colombia": "COL", "Comoros": "COM", "Congo, Dem. Rep.": "COD", "Congo, Rep.": "COG",
    "Costa Rica": "CRI", "Cote d'Ivoire": "CIV", "Croatia": "HRV", "Cuba": "CUB", "Curacao": "CUW",
    "Cyprus": "CYP", "Czechia": "CZE", "Denmark": "DNK", "Djibouti": "DJI", "Dominica": "DMA",
    "Dominican Republic": "DOM", "Ecuador": "ECU", "Egypt, Arab Rep.": "EGY", "El Salvador": "SLV", "Equatorial Guinea": "GNQ",
    "Eritrea": "ERI", "Estonia": "EST", "Eswatini": "SWZ", "Ethiopia": "ETH", "Faroe Islands": "FRO",
    "Fiji": "FJI", "Finland": "FIN", "France": "FRA", "French Polynesia": "PYF", "Gabon": "GAB",
    "Gambia, The": "GMB", "Georgia": "GEO", "Germany": "DEU", "Ghana": "GHA", "Gibraltar": "GIB",
    "Greece": "GRC", "Greenland": "GRL", "Grenada": "GRD", "Guam": "GUM", "Guatemala": "GTM",
    "Guinea": "GIN", "Guinea-Bissau": "GNB", "Guyana": "GUY", "Haiti": "HTI", "Honduras": "HND",
    "Hong Kong SAR, China": "HKG", "Hungary": "HUN", "Iceland": "ISL", "India": "IND", "Indonesia": "IDN",
    "Iran, Islamic Rep.": "IRN", "Iraq": "IRQ", "Ireland": "IRL", "Isle of Man": "IMN", "Israel": "ISR",
    "Italy": "ITA", "Jamaica": "JAM", "Japan": "JPN", "Jordan": "JOR", "Kazakhstan": "KAZ",
    "Kenya": "KEN", "Kiribati": "KIR", "Korea, Dem. People's Rep.": "PRK", "Korea, Rep.": "KOR", "Kosovo": "XKX",
    "Kuwait": "KWT", "Kyrgyz Republic": "KGZ", "Lao PDR": "LAO", "Latvia": "LVA", "Lebanon": "LBN",
    "Lesotho": "LSO", "Liberia": "LBR", "Libya": "LBY", "Liechtenstein": "LIE", "Lithuania": "LTU",
    "Luxembourg": "LUX", "Macao SAR, China": "MAC", "Madagascar": "MDG", "Malawi": "MWI", "Malaysia": "MYS",
    "Maldives": "MDV", "Mali": "MLI", "Malta": "MLT", "Marshall Islands": "MHL", "Mauritania": "MRT",
    "Mauritius": "MUS", "Mexico": "MEX", "Micronesia, Fed. Sts.": "FSM", "Moldova": "MDA", "Monaco": "MCO",
    "Mongolia": "MNG", "Montenegro": "MNE", "Morocco": "MAR", "Mozambique": "MOZ", "Myanmar": "MMR",
    "Namibia": "NAM", "Nauru": "NRU", "Nepal": "NPL", "Netherlands": "NLD", "New Caledonia": "NCL",
    "New Zealand": "NZL", "Nicaragua": "NIC", "Niger": "NER", "Nigeria": "NGA", "North Macedonia": "MKD",
    "Northern Mariana Islands": "MNP", "Norway": "NOR", "Oman": "OMN", "Pakistan": "PAK", "Palau": "PLW",
    "Panama": "PAN", "Papua New Guinea": "PNG", "Paraguay": "PRY", "Peru": "PER", "Philippines": "PHL",
    "Poland": "POL", "Portugal": "PRT", "Puerto Rico": "PRI", "Qatar": "QAT", "Romania": "ROU",
    "Russian Federation": "RUS", "Rwanda": "RWA", "Samoa": "WSM", "San Marino": "SMR", "Sao Tome and Principe": "STP",
    "Saudi Arabia": "SAU", "Senegal": "SEN", "Serbia": "SRB", "Seychelles": "SYC", "Sierra Leone": "SLE",
    "Singapore": "SGP", "Sint Maarten (Dutch part)": "SXM", "Slovak Republic": "SVK", "Slovenia": "SVN", "Solomon Islands": "SLB",
    "Somalia": "SOM", "South Africa": "ZAF", "South Sudan": "SSD", "Spain": "ESP", "Sri Lanka": "LKA",
    "St. Kitts and Nevis": "KNA", "St. Lucia": "LCA", "St. Martin (French part)": "MAF", "St. Vincent and the Grenadines": "VCT",
    "Sudan": "SDN", "Suriname": "SUR", "Sweden": "SWE", "Switzerland": "CHE", "Syrian Arab Republic": "SYR",
    "Tajikistan": "TJK", "Tanzania": "TZA", "Thailand": "THA", "Timor-Leste": "TLS", "Togo": "TGO",
    "Tonga": "TON", "Trinidad and Tobago": "TTO", "Tunisia": "TUN", "Turkiye": "TUR", "Turks and Caicos Islands": "TCA",
    "Tuvalu": "TUV", "Uganda": "UGA", "Ukraine": "UKR", "United Arab Emirates": "ARE", "United Kingdom": "GBR",
    "United States": "USA", "Uruguay": "URY", "Uzbekistan": "UZB", "Vanuatu": "VUT", "Venezuela, RB": "VEN",
    "Vietnam": "VNM", "Virgin Islands (U.S.)": "VIR", "West Bank and Gaza": "PSE", "Yemen, Rep.": "YEM",
    "Zambia": "ZMB", "Zimbabwe": "ZWE",
}


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
country_names = list(COUNTRY_OPTIONS)
auto_country_name = next(
    (name for name, code in COUNTRY_OPTIONS.items() if code == auto_country),
    country_names[0],
)

if "country_selector" not in st.session_state:
    st.session_state.country_selector = auto_country_name
if "previous_primary_ticker" not in st.session_state:
    st.session_state.previous_primary_ticker = primary_ticker
if primary_ticker != st.session_state.previous_primary_ticker:
    st.session_state.country_selector = auto_country_name
    st.session_state.previous_primary_ticker = primary_ticker

selected_country_name = st.sidebar.selectbox(
    "World Bank country",
    options=country_names,
    key="country_selector",
    help="Choose a country from the full World Bank country list. It defaults from the primary ticker.",
)
selected_country_code = COUNTRY_OPTIONS[selected_country_name]
manual_country_code = st.sidebar.text_input(
    "Manual ISO-3 override (optional)",
    value="",
    max_chars=3,
    help="Enter a three-letter World Bank country code to override the dropdown, including codes not listed above.",
).strip().upper()
country_code = manual_country_code or selected_country_code
if manual_country_code and (len(manual_country_code) != 3 or not manual_country_code.isalpha()):
    st.sidebar.warning("Use a three-letter ISO-3 country code, such as TWN or USA.")

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