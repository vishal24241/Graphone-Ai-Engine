from datetime import datetime, timezone, timedelta

from src.extraction.fresh_parser import parse_date, is_fresh


def test_parse_iso_date():
    result = parse_date("2026-08-18T10:00:00Z")
    assert result is not None
    assert result.tzinfo is not None


def test_parse_rfc_date():
    result = parse_date("Tue, 18 Aug 2026 10:00:00 GMT")
    assert result is not None
    assert result.tzinfo is not None


def test_invalid_date():
    assert parse_date("not-a-date") is None


def test_recent_date_is_fresh():
    dt = datetime.now(timezone.utc) - timedelta(hours=1)
    assert is_fresh(dt) is True


def test_old_date_is_not_fresh():
    dt = datetime.now(timezone.utc) - timedelta(hours=25)
    assert is_fresh(dt) is False
