# Data Sources Template

Maintain one row per source, dataset, or API endpoint used by the dashboard.

| Field | Record |
| --- | --- |
| Provider | Name of vendor, exchange, or internal system |
| Dataset / endpoint | Exact product, table, or API route |
| Fields used | Symbols, prices, FX rates, classifications, etc. |
| Coverage | Markets, instruments, and date range |
| Frequency | Intraday, end-of-day, monthly, etc. |
| Retrieval time | Time zone and timestamp |
| Transformations | Cleaning, mapping, adjustments, and joins |
| Quality checks | Missingness, duplicates, outliers, and reconciliation |
| License / rights | Permitted usage and redistribution constraints |
| Owner | Team or individual accountable for the feed |

## Example data-lineage entry

Use a dated entry for every refresh that materially changes the dashboard. Retain the source version and any failed validation results so outputs can be reproduced.
