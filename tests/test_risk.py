import pandas as pd
import pytest

from src.risk import coverage_aware_percentiles, score_company


def test_score_company_reports_weighted_components_and_full_coverage():
    score = score_company(
        {
            "returnOnEquity": 0.20,
            "operatingMargins": 0.25,
            "profitMargins": 0.15,
            "revenueGrowth": 0.10,
            "currentRatio": 1.5,
            "quickRatio": 1.0,
            "debtToEquity": 50,
        }
    )

    assert score["overall_score"] is not None
    assert score["fundamental_coverage"] == 1.0
    assert score["liquidity_coverage"] == 1.0
    assert score["coverage"] == 1.0
    assert score["fundamental_components"]["returnOnEquity"] == pytest.approx(66.6667, abs=0.001)
    assert score["liquidity_components"]["debtToEquity"] == 75.0


def test_missing_metrics_reduce_coverage_without_imputation():
    score = score_company({"returnOnEquity": 0.20, "currentRatio": 1.5})

    assert score["fundamental_coverage"] == pytest.approx(0.35)
    assert score["liquidity_coverage"] == pytest.approx(0.40)
    assert score["coverage"] == pytest.approx(0.375)
    assert score["fundamental_components"]["operatingMargins"] is None
    assert score["liquidity_components"]["quickRatio"] is None


def test_percentile_excludes_insufficient_coverage():
    frame = pd.DataFrame(
        {
            "ticker": ["A", "B", "C"],
            "overall_score": [80.0, 99.0, 60.0],
            "coverage": [1.0, 0.25, 0.75],
        }
    )

    result = coverage_aware_percentiles(frame, minimum_coverage=0.50)

    assert result.loc[0, "percentile"] == 100.0
    assert result.loc[2, "percentile"] == 50.0
    assert pd.isna(result.loc[1, "percentile"])
    assert not bool(result.loc[1, "percentile_eligible"])
