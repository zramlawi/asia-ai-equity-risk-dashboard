# Asia AI Equity Risk Dashboard

A starter project for monitoring Asia-listed AI-related equities and surfacing portfolio-level risk signals. The project is intentionally data-provider agnostic: the included CSV is a watchlist template, while the Python modules validate data, calculate basic risk metrics, and prepare dashboard-ready tables.

## What this starter includes

- A configurable Asia AI equity watchlist in `data/tickers.csv`
- Reusable Python modules for loading data and calculating returns, volatility, drawdowns, and risk flags
- A notebook scaffold for exploratory analysis
- Documentation templates for methodology, data sources, and a risk register

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -c "from src.data import load_tickers; print(load_tickers().head())"
```

## Project layout

```text
.
├── data/tickers.csv
├── docs/
├── notebooks/01_exploratory_analysis.ipynb
├── src/
│   ├── data.py
│   ├── risk.py
│   └── config.py
├── requirements.txt
└── .gitignore
```

## Notes

The included tickers are examples only. They are not investment advice, do not contain live prices, and should be verified with your chosen market-data provider before use. See `docs/methodology.md` for assumptions and `docs/data-sources.md` for data-governance guidance.

## License

Add a license appropriate to your intended use before distribution.
