# Asia AI Equity Risk Dashboard

A Streamlit starter project for monitoring Asia-listed AI-related equities and surfacing basic portfolio-level risk signals. It is intentionally data-provider agnostic in its watchlist design; the runnable app uses Yahoo Finance through `yfinance` for a convenience data feed.

## What this includes

- A configurable Asia AI equity watchlist in `data/tickers.csv`
- A runnable Streamlit app in `app.py`
- Reusable Python modules for loading data and calculating returns, volatility, drawdowns, and risk flags
- A notebook scaffold for exploratory analysis
- Documentation templates for methodology, data sources, and a risk register

## Quick start

```bash
git clone https://github.com/zramlawi/asia-ai-equity-risk-dashboard.git
cd asia-ai-equity-risk-dashboard

python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Streamlit prints a local browser address, typically `http://localhost:8501`. In the app, select countries and a history period, then choose **Load market data**.

## Project layout

```text
.
├── app.py
├── data/tickers.csv
├── docs/
├── notebooks/01_exploratory_analysis.ipynb
├── src/
│   ├── config.py
│   ├── data.py
│   └── risk.py
├── requirements.txt
└── .gitignore
```

## Dashboard behavior

The app displays the selected watchlist, downloads historical adjusted-close prices on demand, then calculates annualized volatility, maximum drawdown, observation counts, and a configurable volatility review flag. Price lines are normalized to 100 at each security’s first available observation.

The ticker file intentionally includes a few local-listing/ADR combinations as review examples. The app flags companies with multiple listings to help prevent double counting. Verify ticker coverage, corporate actions, currencies, and data licenses with your preferred data provider before relying on results.

## Notes

The included tickers and metrics are examples only. They are not investment advice and do not represent a recommendation to buy, sell, or hold any security. See `docs/methodology.md` for assumptions and `docs/data-sources.md` for data-governance guidance.

## License

Add a license appropriate to your intended use before distribution.
