"""UTC time parsing and STK UTCG formatting."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from .errors import StkValidationError

UTC = timezone.utc

_STK_FORMATS = (
    "%d %b %Y %H:%M:%S.%f",
    "%d %b %Y %H:%M:%S",
    "%d %B %Y %H:%M:%S.%f",
    "%d %B %Y %H:%M:%S",
    "%d %b %Y",
    "%d %B %Y",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y",
)


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def parse_time(value: str | date | datetime | None, *, default: datetime | None = None) -> datetime:
    """Parse common STK / ISO / human date strings into an aware UTC datetime."""
    if value is None:
        if default is None:
            raise StkValidationError("time value is required")
        return default
    if isinstance(value, datetime):
        return ensure_utc(value)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=UTC)

    text = str(value).strip()
    if not text:
        if default is None:
            raise StkValidationError("time value is empty")
        return default
    lowered = text.lower()
    if lowered in {"now", "current"}:
        return datetime.now(UTC)
    if lowered in {"today"}:
        now = datetime.now(UTC)
        return datetime(now.year, now.month, now.day, tzinfo=UTC)

    # STK strings are often suffixed with UTCG or prefixed with "UTCG ".
    if lowered.endswith("utcg"):
        text = text[:-4].strip()
    if lowered.startswith("utcg "):
        text = text[5:].strip()

    iso = text.replace("Z", "+00:00")
    try:
        return ensure_utc(datetime.fromisoformat(iso))
    except ValueError:
        pass

    for fmt in _STK_FORMATS:
        try:
            return ensure_utc(datetime.strptime(text, fmt))
        except ValueError:
            continue

    raise StkValidationError(
        f"Unrecognized time value: {value!r}",
        hint="Use ISO-8601 (2026-01-01T00:00:00Z) or STK UTCG "
        "(1 Jan 2026 00:00:00.000).",
    )


def format_stk(value: datetime) -> str:
    """Format as STK's canonical UTCG string, e.g. ``1 Jan 2026 00:00:00.000``."""
    dt = ensure_utc(value)
    millis = dt.microsecond // 1000
    return f"{dt.day} {dt.strftime('%b %Y %H:%M:%S')}.{millis:03d}"


def format_iso(value: datetime) -> str:
    dt = ensure_utc(value)
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def format_time_pair(start: datetime, stop: datetime) -> dict[str, str]:
    return {
        "start": format_stk(start),
        "stop": format_stk(stop),
        "start_iso": format_iso(start),
        "stop_iso": format_iso(stop),
    }


def duration_seconds(start: datetime, stop: datetime) -> float:
    return (ensure_utc(stop) - ensure_utc(start)).total_seconds()


def add_hours(value: datetime, hours: float) -> datetime:
    return ensure_utc(value) + timedelta(hours=hours)


def resolve_interval(
    start: str | datetime | None,
    stop: str | datetime | None,
    *,
    default_start: datetime,
    duration_hours: float,
) -> tuple[datetime, datetime]:
    """Resolve an optional [start, stop] pair, applying the default duration."""
    start_dt = parse_time(start, default=default_start)
    if stop is not None:
        stop_dt = parse_time(stop)
    else:
        stop_dt = start_dt + timedelta(hours=duration_hours)
    if stop_dt <= start_dt:
        raise StkValidationError("stop time must be later than start time")
    return start_dt, stop_dt
