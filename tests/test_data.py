from datetime import datetime, timedelta, timezone

from src.data import _field_record, freshness_status, normalize_world_bank, ticker_to_country


def test_ticker_country_mapping_and_override():
    assert ticker_to_country("005930.KS") == "KOR"
    assert ticker_to_country("0700.HK") == "CHN"
    assert ticker_to_country("unknown") == "WLD"
    assert ticker_to_country("TSM", "usa") == "USA"


def test_freshness_status_marks_old_quotes_stale():
    now = datetime(2026, 1, 2, tzinfo=timezone.utc)
    fresh = freshness_status(now - timedelta(hours=2), now=now)
    stale = freshness_status(now - timedelta(hours=40), now=now)
    missing = freshness_status(None, now=now)
    assert fresh.is_fresh is True
    assert fresh.age_hours == 2
    assert stale.is_fresh is False
    assert "stale" in stale.message
    assert missing.is_fresh is False


def test_field_record_excludes_stale_or_missing_values_from_scoring():
    now = datetime(2026, 1, 2, tzinfo=timezone.utc)
    live = _field_record(10.0, freshness_status(now - timedelta(hours=1), now=now))
    stale = _field_record(10.0, freshness_status(now - timedelta(hours=40), now=now))
    missing = _field_record(None, freshness_status(now - timedelta(hours=1), now=now))
    assert live["data_state"] == "live" and live["scoring_eligible"]
    assert stale["data_state"] == "stale" and not stale["scoring_eligible"]
    assert missing["data_state"] == "missing" and not missing["scoring_eligible"]


def test_normalize_world_bank_removes_null_values_and_sorts():
    records = [
        {"date": "2024", "value": 3.1, "country": {"value": "Taiwan, China"}, "countryiso3code": "TWN"},
        {"date": "2023", "value": None, "country": {"value": "Taiwan, China"}, "countryiso3code": "TWN"},
        {"date": "2022", "value": 2.4, "country": {"value": "Taiwan, China"}, "countryiso3code": "TWN"},
    ]
    frame = normalize_world_bank(records, "GDP growth (%)")
    assert frame["year"].tolist() == [2022, 2024]
