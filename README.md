# Asia & U.S. Equity Risk Dashboard

A Streamlit dashboard for comparing curated Asian and U.S. market/company instruments, custom tickers, price behavior, and a transparent market-behavior speculation signal. It is for education and scenario analysis—not investment advice.

## Features

- Region-specific **Asian Pacific** and **United States** market selectors.
- Curated company presets: TSMC, Samsung, Toyota, Sony, Tencent, Alibaba, Infosys; NVIDIA, Microsoft, Apple, Amazon, Alphabet, Meta, and Tesla.
- Comma-separated custom ticker support, including Yahoo Finance exchange suffixes such as `7203.T`.
- Price-performance, risk-return, momentum-versus-fundamentals, and peer-comparison Plotly charts.
- A transparent 0–100 speculation signal with component weights and explanation labels.
- Yahoo Finance retrieval through `yfinance`, with deterministic synthetic price paths if data are unavailable. Fallback series are clearly identified and must not be interpreted as live market data.

## Speculation signal

The signal reflects observable price behavior, not value, quality, or a prediction. Its score is:

- 45 points: six-month price momentum, capped at 60%.
- 35 points: annualized trailing 63-trading-day volatility, capped at 80%.
- 20 points: maximum drawdown, capped at 35%.

Scores below 34 are labeled lower, 34–66 moderate, and 67+ high speculation signal.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Test

```bash
pytest -q
```

## Data behavior

The app attempts Yahoo Finance first. A network error, delisted symbol, rate limit, or insufficient price history activates a deterministic fallback path. The fallback enables the interface and tests to work safely offline, but it is deliberately labeled so it cannot be mistaken for actual market history.
