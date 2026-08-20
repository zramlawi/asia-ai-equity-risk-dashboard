import pandas as pd

from src.analytics import (
    available_tickers,
    load_price_frame,
    normalize_tickers,
    peer_comparison,
    risk_return,
    speculation_signal,
    synthetic_prices,
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
    assert (first > 0).all()


def test_load_price_frame_has_safe_shape_when_yahoo_is_unavailable(monkeypatch):
    monkeypatch.setattr("src.analytics.load_prices", lambda ticker, period: type("Result", (), {"prices": synthetic_prices(ticker, 40), "source": "Deterministic fallback", "note": "offline"})())
    frame, results = load_price_frame(["NVDA", "TSM"])
    assert list(frame.columns) == ["NVDA", "TSM"]
    assert all(item.source == "Deterministic fallback" for item in results.values())


def test_risk_return_and_peer_comparison_are_populated():
    frame = pd.concat([synthetic_prices("NVDA"), synthetic_prices("TSM")], axis=1)
    metrics = risk_return(frame)
    peers = peer_comparison(frame)
    assert set(metrics.columns) == {"annual_return", "annual_volatility"}
    assert set(peers["ticker"]) == {"NVDA", "TSM"}


def test_speculation_signal_is_bounded_and_explained():
    signal = speculation_signal(synthetic_prices("NVDA", periods=252))
    assert 0 <= signal["score"] <= 100
    assert "momentum" in signal["explanation"].lower()
    assert signal["label"] in {"Lower speculation signal", "Moderate speculation signal", "High speculation signal"}
