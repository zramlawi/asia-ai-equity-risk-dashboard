from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
TICKERS_PATH = DATA_DIR / "tickers.csv"

REQUIRED_TICKER_COLUMNS = {
    "ticker",
    "company",
    "country",
    "exchange",
    "currency",
    "sector",
    "theme",
    "market_cap_bucket",
}
