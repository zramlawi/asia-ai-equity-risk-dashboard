# Price-Risk Methodology

## Purpose

This dashboard is a **relative price-risk screen** for a selected universe of Asian AI, semiconductor, and technology equities. It highlights securities with a combination of recent price strength, technical extension, volatility, and drawdown behavior. It does not estimate intrinsic value, forecast returns, or diagnose a financial bubble.

## Market data

At refresh time, the app requests approximately two years of daily auto-adjusted close data through Yahoo Finance and the `yfinance` Python package. A ticker must have at least 210 daily observations to enter the calculations. Tickers that return no data or insufficient history appear in the failed-download table and receive no substituted score.

Yahoo Finance data may be delayed, incomplete, revised, or unavailable. The returned history, market holidays, corporate-action treatment, and ticker coverage can differ by exchange and over time.

## Observed metrics

For each successfully downloaded security, the dashboard calculates:

- **3-, 6-, and 12-month return:** percent change over 63, 126, and 252 trading sessions, respectively.
- **50-day and 200-day moving-average distance:** latest close divided by the corresponding simple moving average, minus one.
- **Distance from trailing high:** latest close divided by the highest close in the returned history, minus one.
- **Annualized volatility:** standard deviation of daily returns multiplied by the square root of 252.
- **Maximum drawdown:** worst percentage decline from a preceding running high within the returned history.

## Score construction

Each factor is converted to a percentile rank across only the securities with valid downloads in the current refresh. The 0–100 score is the following weighted sum:

\[
Score = 0.30P(R_{6m}) + 0.20P(D_{200}) + 0.15P(D_{high}) + 0.20P(Vol) + 0.15P(-MDD)
\]

where:

- \(P\) is the cross-sectional percentile rank.
- \(R_{6m}\) is six-month return.
- \(D_{200}\) is distance from the 200-day moving average.
- \(D_{high}\) is distance from the trailing high; securities closer to their high rank higher.
- \(Vol\) is annualized historical volatility.
- \(MDD\) is maximum drawdown; a more negative drawdown ranks as greater realized risk.

The display bands are Lower (0–40), Elevated (>40–70), and High (>70). They are labels for screen navigation, not investment ratings.

## Interpretation and limits

A high score means the name ranks high in one or more price-extension or realized-risk characteristics **relative to the loaded watchlist**. It does not mean the price is unsustainable, and a low score does not mean a security is safe or attractive.

The model intentionally excludes valuation multiples, profitability, earnings revisions, cash flow, leverage, analyst expectations, options positioning, trading liquidity, governance, country risk, currency movements, and other fundamental or macroeconomic inputs. A dependable fundamentals provider and a separate methodology are required before adding those dimensions.

The dashboard is for research and education only, not personalized investment advice, a recommendation, or a solicitation to buy or sell securities.
