from __future__ import annotations

from datetime import datetime, timezone

import pytest

from spaceone_stk_mcp.errors import StkValidationError
from spaceone_stk_mcp.timeutil import format_iso, format_stk, parse_time


@pytest.mark.parametrize(
    "value",
    [
        "1 Jan 2026 00:00:00.000",
        "01 Jan 2026 00:00:00",
        "2026-01-01T00:00:00Z",
        "2026-01-01T00:00:00+00:00",
        "2026-01-01 00:00:00",
        "2026-01-01",
        "1 January 2026",
    ],
)
def test_parse_time_variants(value):
    parsed = parse_time(value)
    assert parsed.year == 2026
    assert parsed.month == 1
    assert parsed.day == 1
    assert parsed.tzinfo is not None


def test_parse_time_default_and_now():
    default = datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert parse_time(None, default=default) == default
    now = parse_time("now")
    assert now.year >= 2024


def test_format_round_trip():
    dt = parse_time("2026-01-01T12:34:56.789Z")
    assert format_stk(dt) == "1 Jan 2026 12:34:56.789"
    assert format_iso(dt) == "2026-01-01T12:34:56.789Z"
    assert parse_time(format_stk(dt)) == dt


def test_bad_time():
    with pytest.raises(StkValidationError):
        parse_time("not-a-date")
