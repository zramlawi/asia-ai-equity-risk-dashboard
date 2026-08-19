# Free-data methodology

## Sources and hierarchy

The application uses Yahoo Finance through `yfinance` for adjusted daily prices and quote-summary fundamentals. World Bank Open Data supplies country-level macro indicators through its public API. Alpha Vantage `OVERVIEW` is an optional enrichment source only when `ALPHA_VANTAGE_API_KEY` is present in a local environment or secret manager. Yahoo data is primary for issuer fundamentals; Alpha Vantage fills only missing mapped fields and never overwrites a Yahoo value.

No credentials, proprietary datasets, or synthetic/fallback fundamentals are stored in the repository. Provider status records whether a source is available, partial, disabled, no-data, or unavailable and records the retrieval time; World Bank fields also record their observation year.

## Fields

Yahoo Finance fields include market capitalization, trailing and forward P/E, price/book, EV/EBITDA, EPS, ROE, profit margin, revenue and earnings growth, cash, debt, current and quick ratios, operating and free cash flow, share count, average volume, and 52-week range when reported. All absent fields are shown as not reported rather than estimated.

World Bank indicators are GDP growth (`NY.GDP.MKTP.KD.ZG`), CPI inflation (`FP.CPI.TOTL.ZG`), unemployment (`SL.UEM.TOTL.ZS`), current-account balance as a share of GDP (`BN.CAB.XOKA.GD.ZS`), and official exchange rate (`PA.NUS.FCRF`). Values are latest available annual observations; they are not necessarily from a common calendar year.

## Calculations

Price risk reports close-price history, maximum drawdown `close / cumulative maximum(close) - 1`, and annualized realized volatility `standard deviation(daily returns) × sqrt(252)`.

Fundamental Stretch is a 0–100 equal-weight mean of available normalized components: trailing P/E (10–50), price/book (1–10), EV/EBITDA (5–30), and inverse-risk components for ROE (5–30%), profit margin (2–25%), revenue growth (-10–30%), and earnings growth (-20–40%). Higher values indicate greater valuation stretch or weaker reported fundamentals relative to these transparent ranges.

Liquidity Risk is a 0–100 equal-weight mean of available normalized components: inverse average daily dollar volume (USD 1m–100m), inverse current ratio (0.5–2.0), and inverse quick ratio (0.3–1.5). Average daily dollar volume is latest price multiplied by reported average volume. Higher values indicate potentially weaker trading or balance-sheet liquidity. Every component is clipped to 0–100. Missing components are excluded, never imputed; a score can therefore be unavailable or based on partial coverage.

Coverage is `available fields / total tracked fields × 100`. It should be read alongside provider status and field-level missing messages.

## Licenses and limitations

Users must comply with Yahoo Finance, `yfinance`, World Bank, and Alpha Vantage terms. Free data may be delayed, adjusted, revised, incomplete, rate-limited, or unavailable. Corporate-accounting definitions and currencies can differ across issuers. Country macro data is not a real-time market signal. The dashboard does not provide analyst estimates, options, short interest, institutional ownership, or live geopolitical-event data.

## Non-advice disclaimer

This dashboard is educational research software, not investment, legal, tax, or financial advice. Scores are heuristic and cannot predict returns, bubbles, liquidity events, or macro outcomes. Verify data with authoritative issuer filings and qualified professionals before making decisions.
