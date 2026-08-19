# Bubble-risk methodology

## Purpose

This dashboard is a transparent **scenario-analysis tool**, not a forecast, valuation model, credit rating, or investment recommendation. It ranks the relative downside sensitivity of companies in the supplied universe when a broad technology risk-off event coincides with AI-related valuation compression and earnings disappointment.

## Inputs

The dashboard reads `data/tickers.csv`. The only required columns are:

- `country`
- `ticker`
- `name`

It optionally uses the following numeric fields (including documented aliases in `src/bubble.py`):

- **Valuation risk**: indicators such as valuation premium, valuation percentile, or a precomputed 0–100 score.
- **Earnings risk**: indicators such as revision pressure, a normalized earnings score, or a precomputed 0–100 score.
- **Market risk**: indicators such as volatility, beta, or a normalized market-risk score.
- **AI exposure**: indicators such as AI revenue share or a normalized AI-exposure score.

Each available input is transformed to a 0–1 scale. Values already on a 0–1 scale are retained; values on a 0–100 scale are divided by 100; other numeric series are min–max normalized within the loaded universe. Missing values, and entirely absent optional columns, receive neutral defaults: valuation 0.55, earnings 0.45, market 0.50, and AI exposure 0.50. This allows a basic ticker universe to run, but it also makes results less company-specific.

## Risk score

The company-level base score uses fixed factor weights:

\[B = 0.35V + 0.25E + 0.25M + 0.15A\]

where \(V\), \(E\), \(M\), and \(A\) are the normalized valuation, earnings, market, and AI-exposure factors. The scenario intensity is:

\[S = 0.40\min(1, |G|/0.40) + 0.35C + 0.25H\]

where \(G\) is the global technology shock, \(C\) is valuation compression, and \(H\) is the earnings shortfall. The displayed score is:

\[100B(0.55 + 0.45S)\]

Scores at or below 35 are **Low**, above 35 through 65 are **Moderate**, and above 65 are **High**.

## Scenario drawdown

The displayed scenario drawdown is a stylized sensitivity estimate, not a predicted return. It adds a market-shock component plus valuation- and earnings-shortfall components that increase with both the relevant risk factor and AI exposure. It is capped at -100%.

## Limitations

- The tool does not retrieve live prices, consensus estimates, financial statements, or macroeconomic data.
- The results depend on input-data quality, country coverage, factor definitions, and the selected scenario.
- Normalizing values within the file makes scores relative to the supplied universe, not absolute measures of risk.
- Correlation, liquidity, FX effects, policy changes, portfolio weights, and nonlinear market dynamics are not modeled.
- Do not use the output as the sole basis for an investment decision.
