# Asia AI Equity Risk Dashboard

A local Streamlit dashboard for transparent, scenario-based review of downside sensitivity in a selected Asian equity universe. It is an educational research tool—not investment advice.

## What it does

- Loads the company universe from `data/tickers.csv`.
- Lets you select countries and adjust three downside scenario controls.
- Calculates a 0–100 bubble-risk score and a stylized scenario drawdown.
- Shows country-level averages and a company-level review table.
- Documents the assumptions and limitations in [`docs/bubble-risk-methodology.md`](docs/bubble-risk-methodology.md).

## Requirements

Use Python 3.10 or later. The included `requirements.txt` should include at least:

```text
streamlit
pandas
numpy
```

## Setup

```bash
git clone https://github.com/zramlawi/asia-ai-equity-risk-dashboard.git
cd asia-ai-equity-risk-dashboard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

## Run

```bash
streamlit run app.py
```

Streamlit will print a local address, usually `http://localhost:8501`. Open that address in your browser.

## Updating an existing clone

```bash
git pull origin main
pip install -r requirements.txt
streamlit run app.py
```

If you downloaded a ZIP instead of cloning, download a new ZIP from the repository after the update, extract it into a fresh folder, and then run the setup commands above.

## Data format

`data/tickers.csv` must include these columns:

```text
country,ticker,name
```

Optional numeric fields make the analysis more specific: `valuation_risk`, `earnings_risk`, `market_risk`, and `ai_exposure`. Values may be expressed as 0–1 proportions or 0–100 scores. See the methodology document for factor aliases, default values, scoring formula, and limitations.

## Troubleshooting

- `SyntaxError` on line 1: ensure you are using the updated `app.py`, not an older extracted ZIP.
- `ModuleNotFoundError`: activate the virtual environment and run `pip install -r requirements.txt`.
- `streamlit: command not found`: use `python -m streamlit run app.py` after installing dependencies.
- Data-load error: confirm `data/tickers.csv` exists and contains `country`, `ticker`, and `name`.
