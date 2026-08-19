# Asia AI Equity Risk Dashboard

A Streamlit research dashboard for public-market price risk, reported fundamentals, liquidity context, and country macro indicators. It is designed to run with **free public sources** and does not provide investment advice.

## Free-data setup

```bash
git clone https://github.com/zramlawi/asia-ai-equity-risk-dashboard.git
cd asia-ai-equity-risk-dashboard
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

The dashboard works without a key using Yahoo Finance price/quote data and World Bank Open Data. Enter a Yahoo-compatible ticker and a World Bank three-letter economy code, for example `TSM` / `TWN`, `005930.KS` / `KOR`, or `7203.T` / `JPN`.

## Optional Alpha Vantage

Alpha Vantage is disabled by default. To enable its optional OVERVIEW enrichment locally, copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and add a personal key, or set `ALPHA_VANTAGE_API_KEY` in the environment. Never commit a real key; `.streamlit/secrets.toml` and `.env` are ignored.

## Dashboard modules

- **Price Risk:** Yahoo Finance close-price chart, max drawdown, and realized annualized volatility.
- **Fundamentals & Liquidity:** reported valuation, profitability, balance-sheet, and trading-liquidity fields; 0–100 Fundamental Stretch and Liquidity Risk scores.
- **Country Macro:** World Bank GDP growth, CPI inflation, unemployment, current-account balance, and official exchange-rate context.
- **Data Quality:** source names, timestamps, field coverage, provider status, missing-data explanations, and provider-required datasets.

## Limitations

Yahoo Finance data can be delayed, incomplete, unavailable for particular exchanges, or subject to symbol mapping differences. World Bank macro indicators are annual and released on different schedules; the latest observation year can vary by indicator. Alpha Vantage free access can be rate-limited. The app does not fabricate or impute missing fundamentals.

Analyst estimates, options, short interest, institutional ownership, and live geopolitical-event scoring remain visibly unavailable because they require suitable providers. See [free-data methodology](docs/free-data-methodology.md) and [bubble-risk methodology](docs/bubble-risk-methodology.md).

## Deployment

For local use, keep keys in environment variables or untracked Streamlit secrets. For a public Streamlit deployment, configure `ALPHA_VANTAGE_API_KEY` only in the host’s secret manager. A public deployment can run without that secret but must disclose source latency, coverage gaps, and the non-advice limitation.

## Troubleshooting

- **No price data:** confirm the Yahoo Finance ticker suffix and retry later.
- **Partial fundamentals:** the issuer or exchange may not report a field through the free sources; consult the Data Quality tab.
- **No macro data:** verify the World Bank three-letter economy code, such as `TWN`, `KOR`, `JPN`, or `CHN`.
- **Alpha Vantage unavailable:** verify the key is configured privately and account for free-tier request limits.
