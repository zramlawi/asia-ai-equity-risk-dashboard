from __future__ import annotations

TICKER_COUNTRY_MAP = {
    "TSM": "TWN",
    "2330.TW": "TWN",
    "005930.KS": "KOR",
    "9984.T": "JPN",
    "BABA": "CHN",
    "0700.HK": "CHN",
    "INFY.NS": "IND",
    "TCEHY": "CHN",
    "ASML": "NLD",
}

DEFAULT_COUNTRY_CODE = "WLD"
MAX_YAHOO_AGE_HOURS = 36
WORLD_BANK_BASE_URL = "https://api.worldbank.org/v2"
WORLD_BANK_INDICATORS = {
    "GDP growth (%)": "NY.GDP.MKTP.KD.ZG",
    "Inflation (%)": "FP.CPI.TOTL.ZG",
    "Unemployment (%)": "SL.UEM.TOTL.ZS",
}

FUNDAMENTAL_WEIGHTS = {
    "returnOnEquity": 0.35,
    "operatingMargins": 0.30,
    "profitMargins": 0.20,
    "revenueGrowth": 0.15,
}

LIQUIDITY_WEIGHTS = {
    "currentRatio": 0.40,
    "quickRatio": 0.30,
    "debtToEquity": 0.30,
}
