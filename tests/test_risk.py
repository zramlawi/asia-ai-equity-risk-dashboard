import pandas as pd
import pytest

from src.risk import contribution_frame, coverage_aware_percentiles, regime_adjustment, score_company


def live_metrics():
    fields = {
        "momentum_3m": 0.15, "momentum_6m": 0.30, "trailingPE": 20, "forwardPE": 18,
        "priceToBook": 3, "enterpriseToEbitda": 12, "returnOnEquity": 0.20,
        "operatingMargins": 0.25, "profitMargins": 0.15, "revenueGrowth": 0.10,
        "freeCashflow": 5e9, "relative_volume": 1.2, "volume_growth": 0.10,
        "annual_volatility": 0.30, "max_drawdown": -0.15, "debtToEquity": 50,
    }
    return {**fields, **{f"{key}_eligible": True for key in fields}}


def test_score_company_reports_five_pillars_and_full_coverage():
    score = score_company(live_metrics())
    assert score["overall_score"] is not None
    assert score["coverage"] == pytest.approx(1.0)
    assert score["scoring_eligible"] is True
    for pillar in ["price", "valuation", "fundamentals", "activity_volume", "fragility"]:
        assert score[f"{pillar}_score"] is not None
        assert score[f"{pillar}_coverage"] == pytest.approx(1.0)


def test_ineligible_fallback_evidence_does_not_score():
    metrics = live_metrics()
    metrics["momentum_3m_eligible"] = False
    metrics["momentum_6m_eligible"] = False
    score = score_company(metrics)
    assert score["price_score"] is None
    assert score["price_coverage"] == 0


def test_percentile_excludes_insufficient_coverage():
    frame = pd.DataFrame({"ticker": ["A", "B", "C"], "overall_score": [80.0, 99.0, 60.0], "coverage": [1.0, 0.25, 0.75], "scoring_eligible": [True, False, True]})
    result = coverage_aware_percentiles(frame, minimum_coverage=0.50)
    assert result.loc[0, "percentile"] == 100.0
    assert result.loc[2, "percentile"] == 50.0
    assert pd.isna(result.loc[1, "percentile"])


def test_regime_rules_and_contributions_are_visible():
    metrics = live_metrics()
    metrics["annual_volatility"] = 0.60
    metrics["max_drawdown"] = -0.40
    regime = regime_adjustment(metrics)
    assert regime["points"] == 18.0
    frame = contribution_frame(score_company(metrics))
    assert set(frame["pillar"]) == {"Price", "Valuation", "Fundamentals", "Activity Volume", "Fragility"}
