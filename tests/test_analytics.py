import pandas as pd

from src.analytics import (
    available_tickers, load_price_frame, normalize_tickers, price_features,
    risk_return, speculation_signal, synthetic_prices,
)


def test_normalize_tickers_deduplicates_and_uppercases():
    assert normalize_tickers([" nvda ", "NVDA", "tsm", ""]) == ["NVDA", "TSM"]


def test_available_tickers_includes_market_and_company_presets():
    universe = available_tickers("Asia Pacific")
    assert universe["Japan (Nikkei 225)"] == "^N225"
    assert universe["Taiwan Semiconductor"] == "TSM"


def test_synthetic_prices_are_deterministic_and_business_dated():
    first = synthetic_prices("NVDA", periods=30)
    second = synthetic_prices("NVDA", periods=30)
    pd.testing.assert_series_equal(first, second)
    assert len(first) == 30


def test_fallback_prices_are_ineligible_for_scoring(monkeypatch):
    monkeypatch.setattr("src.analytics.load_prices", lambda ticker, period: type("Result", (), {"prices": synthetic_prices(ticker, 40), "source": "Deterministic fallback", "note": "offline", "scoring_eligible": False})())
    frame, results = load_price_frame(["NVDA", "TSM"])
    assert list(frame.columns) == ["NVDA", "TSM"]
    assert all(not item.scoring_eligible for item in results.values())
    assert not price_features(frame["NVDA"], False)["price_scoring_eligible"]


def test_risk_return_and_speculation_signal_are_populated():
    frame = pd.concat([synthetic_prices("NVDA"), synthetic_prices("TSM")], axis=1)
    metrics = risk_return(frame)
    signal = speculation_signal(frame["NVDA"])
    assert set(metrics.columns) == {"annual_return", "annual_volatility"}
    assert 0 <= signal["score"] <= 100
