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
MINIMUM_EVIDENCE_COVERAGE = 0.50

WORLD_BANK_BASE_URL = "https://api.worldbank.org/v2"
WORLD_BANK_INDICATORS = {
    "GDP growth (%)": "NY.GDP.MKTP.KD.ZG",
    "Inflation (%)": "FP.CPI.TOTL.ZG",
    "Unemployment (%)": "SL.UEM.TOTL.ZS",
}

PILLAR_WEIGHTS = {
    "price": 0.22,
    "valuation": 0.22,
    "fundamentals": 0.24,
    "activity_volume": 0.16,
    "fragility": 0.16,
}

PILLAR_FIELDS = {
    "price": {
        "momentum_3m": 0.45,
        "momentum_6m": 0.55,
    },
    "valuation": {
        "trailingPE": 0.30,
        "forwardPE": 0.25,
        "priceToBook": 0.20,
        "enterpriseToEbitda": 0.25,
    },
    "fundamentals": {
        "returnOnEquity": 0.25,
        "operatingMargins": 0.25,
        "profitMargins": 0.20,
        "revenueGrowth": 0.15,
        "freeCashflow": 0.15,
    },
    "activity_volume": {
        "relative_volume": 0.60,
        "volume_growth": 0.40,
    },
    "fragility": {
        "annual_volatility": 0.40,
        "max_drawdown": 0.35,
        "debtToEquity": 0.25,
    },
}

REGIME_RULES = {
    "elevated_volatility": {
        "threshold": 0.45,
        "adjustment": 8.0,
        "description": "Annualized volatility above 45% adds 8 risk points.",
    },
    "stressed_drawdown": {
        "threshold": -0.30,
        "adjustment": 10.0,
        "description": "Maximum drawdown below -30% adds 10 risk points.",
    },
}
