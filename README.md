# Asia AI Equity Risk Dashboard

A Streamlit research dashboard for examining selected Asian equity proxies alongside country-level macroeconomic context. It is an educational scenario-analysis tool, not investment advice.

## Features

- **Yahoo Finance reliability.** Every quote carries an explicit timestamp-based freshness state. Quotes more than 36 hours old, missing timestamps, and provider failures are displayed as stale or unavailable rather than presented as current.
- **Ticker-to-country mapping.** Common exchange suffixes and selected tickers map automatically to a World Bank ISO-3 country code. The dashboard always provides an editable country-code field for analyst overrides.
- **Optional peer comparison.** Enter comma-separated peers to compare fundamental and liquidity scores. Percentile ranks are shown only for peers meeting the selected minimum evidence-coverage threshold.
- **World Bank context.** The dashboard displays the latest reported GDP growth, inflation, and unemployment observations plus annual history charts for the selected country.
- **Transparent scoring.** Fundamental and liquidity components, normalized scores, weights, and observed-data coverage are visible in the interface. Missing metrics lower coverage; they are not imputed.
- **CSV research snapshots.** Download the peer-scoring table with the latest macro indicators as a CSV file.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Using the dashboard

1. Enter a primary Yahoo Finance ticker.
2. Optionally add comma-separated peer tickers.
3. Review the automatically selected World Bank ISO-3 code and edit it when the issuer's relevant macro context differs from the default mapping.
4. Choose the minimum evidence coverage required for peer percentiles.
5. Select **Refresh data** to retrieve market and macroeconomic observations.
6. Inspect freshness warnings, peer comparisons, macro history, and the downloadable snapshot.

## Data behavior

Yahoo Finance is accessed through `yfinance`. A quote is labelled fresh only when the provider timestamp is no more than 36 hours old. A provider exception, absent timestamp, or stale timestamp is visible to the user. Market data may be delayed or incomplete.

World Bank data is accessed through its public API. The dashboard requests annual observations, drops null values, displays the latest available observation for each indicator, and charts the recent annual history. Country indicators can be published with a lag and may be revised.

## Scoring methodology

Scores are normalized to a 0-100 bounded scale using explicit ranges. The ranges are analytical heuristics, not predictions or investment recommendations.

| Score | Components | Weights |
| --- | --- | --- |
| Fundamental | Return on equity, operating margin, profit margin, revenue growth | 35%, 30%, 20%, 15% |
| Liquidity | Current ratio, quick ratio, debt-to-equity (inverted) | 40%, 30%, 30% |

Each sub-score is a weighted average of observed components only. Its coverage is the sum of weights for available observations. Overall evidence coverage is the average of fundamental and liquidity coverage. A peer receives a percentile only when its coverage meets the user-selected floor.

## Testing

Run the suite locally:

```bash
pytest -q
```

The tests cover ticker-country mapping and overrides, Yahoo timestamp freshness, World Bank normalization, transparent scoring, coverage calculation, and exclusion of low-coverage peers from percentiles. GitHub Actions runs the suite on Python 3.10, 3.11, and 3.12 for pushes and pull requests.
