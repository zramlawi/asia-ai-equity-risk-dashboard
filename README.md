# Asia AI Equity Price-Risk Dashboard

An interactive Streamlit research screen for a focused universe of Asian AI, semiconductor, and major technology companies. It downloads daily market prices from Yahoo Finance at refresh time and calculates transparent, price-derived risk indicators.

> This is a research screen, not investment advice. A high score is not a prediction that a security will fall or that a market bubble exists.

## What it covers

The default watchlist contains 40 companies across Japan, South Korea, Taiwan, China and Hong Kong, India, Singapore, and selected ASEAN markets. Every row in `data/tickers.csv` includes a company, exchange-compatible Yahoo Finance ticker, country, exchange, and theme label.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

Use **Refresh market data** to clear the 30-minute in-app cache and request a new Yahoo Finance download. The dashboard shows the exact UTC time of the latest fetch.

## Data and indicators

The app uses `yfinance` to request roughly two years of daily, auto-adjusted closing-price history. It reports a ticker as failed if Yahoo Finance returns no price series or fewer than 210 daily observations. It never invents a fallback price or risk score.

For each valid ticker, the screen displays:

- Three-, six-, and 12-month returns.
- Distance from the 50-day and 200-day moving averages.
- Distance from the trailing high in the returned history.
- Annualized historical daily-return volatility.
- Maximum drawdown in the returned history.
- A normalized 0–100 relative price-risk score.

See [the methodology](docs/bubble-risk-methodology.md) for the formula and interpretation.

## Limitations and troubleshooting

- Yahoo Finance data can be delayed, incomplete, unavailable, corrected, or revised. Exchange symbols may change.
- Prices are real market observations but are not valuation, earnings, balance-sheet, cash-flow, analyst-estimate, ownership, or liquidity data.
- The risk score is relative to the successfully downloaded current watchlist. It is not comparable to a score from a different watchlist or refresh without context.
- A failed download table identifies symbols that need checking. First verify the ticker suffix and whether the exchange has current Yahoo Finance coverage, then refresh.
- The dashboard requires internet access in its runtime environment. It is not designed to provide an offline market-data feed.

## Project structure

- `data/tickers.csv` — curated watchlist.
- `src/data.py` — watchlist validation, Yahoo Finance download, and quality reporting.
- `src/bubble.py` — price metrics and normalized relative risk score.
- `app.py` — Streamlit user interface.
- `docs/bubble-risk-methodology.md` — score design and limitations.
