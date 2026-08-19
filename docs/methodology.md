# Methodology Template

## Objective

Describe the dashboard decision it supports, its intended users, and the time horizon.

## Universe construction

- Define what qualifies as an Asia AI-related equity.
- Document exchanges, countries, security types, ADR treatment, and exclusion rules.
- State how multiple listings and parent/subsidiary relationships are handled to avoid double counting.

## Price and return conventions

- Identify the price field used (for example, adjusted close).
- State the return frequency, market-calendar treatment, currency convention, and missing-data policy.
- Document corporate-action handling and the source timestamp.

## Risk metrics

| Metric | Proposed calculation | Interpretation |
| --- | --- | --- |
| Annualized volatility | Daily-return standard deviation × sqrt(252) | Dispersion of returns; not a forecast |
| Maximum drawdown | Minimum peak-to-trough decline | Historical loss severity |
| Concentration | Sum of weights by country, sector, theme, or issuer | Exposure clustering |

## Thresholds and review

Record threshold owners, rationale, review frequency, and the escalation path for breached metrics.

## Limitations

List survivorship bias, liquidity constraints, data gaps, currency effects, model uncertainty, and any restrictions on using the output for investment decisions.
