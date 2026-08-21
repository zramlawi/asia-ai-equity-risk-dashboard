# Asia & U.S. Equity Risk Dashboard

A Streamlit dashboard for educational, evidence-aware scenario analysis of selected Asian and U.S. equities and market instruments. It is not investment advice.

## Core multi-signal upgrade

The dashboard replaces its illustrative fundamental proxy with Yahoo Finance fields available through `yfinance`. It combines five pillars:

- **Price:** three- and six-month momentum
- **Valuation:** trailing/forward P/E, price-to-book, and EV/EBITDA
- **Fundamentals:** return on equity, operating and profit margins, revenue growth, and free cash flow
- **Activity/volume:** relative volume and volume change when Yahoo Finance coverage is available
- **Fragility:** annualized volatility, maximum drawdown, and debt-to-equity

## Evidence and data status

Each Yahoo Finance observation is represented as **live**, **stale**, or **missing**. A field is score-eligible only when it is live and fresh (by default, no more than 36 hours old). Missing and stale evidence lowers coverage; it is never silently imputed.

When historical Yahoo Finance prices are unavailable, the app can display deterministic synthetic price paths for chart continuity. Those paths are explicitly labeled **fallback** and are excluded from all scoring and percentile calculations.

## Scoring

Pillar weights are price 22%, valuation 22%, fundamentals 24%, activity/volume 16%, and fragility 16%. The final score is reweighted only over live, score-eligible evidence. Scores with less than 50% weighted evidence are ineligible for peer percentiles.

The dashboard also shows:

- Peer-relative percentile among eligible selected instruments
- Historical-style percentile within the displayed peer score distribution
- Pillar contribution chart
- Regime adjustments: +8 points for annualized volatility above 45% and +10 points for drawdown below -30%

These transparent rules are scenario-analysis aids, not predictions or trading instructions. Yahoo Finance is a public, unofficial source and can be delayed, incomplete, or inconsistent by ticker and exchange.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Test

The repository uses imports from the project root. Run:

```bash
PYTHONPATH=. pytest -q
```
