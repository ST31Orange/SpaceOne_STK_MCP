"""JSON-safe conversion of STK COM values, tables and intervals."""

from __future__ import annotations

import math
from datetime import date, datetime
from typing import Any, Iterable

from .timeutil import format_iso


def parse_scalar(value: Any) -> Any:
    """Best-effort conversion of an STK cell to a JSON scalar."""
    if value is None or isinstance(value, (bool, int, float)):
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return None
        return value
    if isinstance(value, (datetime, date)):
        return format_iso(value if isinstance(value, datetime) else datetime.combine(value, datetime.min.time()))
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return text
        # Keep times and labels as strings; convert plain numeric cells.
        try:
            if text.lower() not in {"nan", "inf", "-inf"} and (
                text.replace(".", "", 1).replace("-", "", 1).replace("+", "", 1).isdigit()
                or ("e" in text.lower() and _is_float(text))
            ):
                number = float(text)
                if math.isnan(number) or math.isinf(number):
                    return None
                return int(number) if number.is_integer() and "." not in text and "e" not in text.lower() else number
        except ValueError:
            pass
        return text
    return str(value)


def _is_float(text: str) -> bool:
    try:
        float(text)
        return True
    except ValueError:
        return False


def jsonable(value: Any, *, depth: int = 0) -> Any:
    """Convert arbitrary STK / pywin32 values into JSON-safe structures."""
    if depth > 8:
        return str(value)
    if value is None or isinstance(value, (bool, int, float, str)):
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return None
        return value
    if isinstance(value, (datetime, date)):
        return format_iso(value if isinstance(value, datetime) else datetime.combine(value, datetime.min.time()))
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, dict):
        return {str(k): jsonable(v, depth=depth + 1) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(v, depth=depth + 1) for v in value]
    # COM safe arrays / iterators frequently expose Count + Item.
    if hasattr(value, "GetValues") and callable(value.GetValues):
        try:
            return [jsonable(v, depth=depth + 1) for v in value.GetValues()]
        except Exception:
            pass
    if hasattr(value, "Count") and hasattr(value, "Item"):
        try:
            return [jsonable(value.Item(i), depth=depth + 1) for i in range(int(value.Count))]
        except Exception:
            pass
    # STK objects: expose their identity instead of an unusable COM repr.
    for attr in ("Path", "InstanceName"):
        try:
            text = getattr(value, attr)
            if text:
                return str(text)
        except Exception:
            pass
    text = str(value)
    if text.startswith("<COMObject") or text.startswith("<unknown>"):
        return text
    return text


def dataset_table(result: Any, *, max_rows: int = 20000) -> dict[str, Any]:
    """Convert an ``IAgDataProviderResult`` into ``{columns, rows, truncated}``."""
    datasets = result.DataSets
    columns: list[str] = []
    values: list[list[Any]] = []
    for i in range(int(datasets.Count)):
        try:
            ds = datasets.Item(i)
        except Exception:
            ds = datasets(i)
        try:
            name = str(ds.ElementName)
        except Exception:
            name = f"col{i}"
        try:
            raw = list(ds.GetValues())
        except Exception:
            raw = []
        columns.append(name)
        values.append(raw)
    row_count = max((len(v) for v in values), default=0)
    truncated = row_count > max_rows
    rows: list[dict[str, Any]] = []
    for row_index in range(min(row_count, max_rows)):
        row: dict[str, Any] = {}
        for col_index, name in enumerate(columns):
            column = values[col_index]
            row[name] = parse_scalar(column[row_index]) if row_index < len(column) else None
        rows.append(row)
    return {"columns": columns, "rows": rows, "row_count": row_count, "truncated": truncated}


def access_intervals(access: Any) -> list[dict[str, Any]]:
    """Return access intervals as normalized UTC strings and seconds."""
    intervals: list[dict[str, Any]] = []
    try:
        collection = access.ComputedAccessIntervalTimes
    except Exception:
        return intervals
    count = int(getattr(collection, "Count", 0) or 0)
    for i in range(count):
        item = None
        try:
            item = collection.GetInterval(i)
        except Exception:
            try:
                item = collection(i)
            except Exception:
                item = None
        if isinstance(item, (tuple, list)) and len(item) >= 2:
            start_raw, stop_raw = item[0], item[1]
        else:
            start_raw = getattr(item, "StartTime", None)
            stop_raw = getattr(item, "StopTime", None)
        if start_raw is None or stop_raw is None:
            continue
        start = str(start_raw)
        stop = str(stop_raw)
        entry: dict[str, Any] = {"start": start, "stop": stop, "index": i}
        try:
            from .timeutil import parse_time

            entry["start_iso"] = format_iso(parse_time(start))
            entry["stop_iso"] = format_iso(parse_time(stop))
            entry["duration_sec"] = (parse_time(stop) - parse_time(start)).total_seconds()
        except Exception:
            pass
        intervals.append(entry)
    return intervals


def describe_com_result(result: Any) -> dict[str, Any]:
    """Describe the opaque object returned by ``IAgStkObjectRoot.ExecuteCommand``."""
    text = str(result)
    payload: dict[str, Any] = {"type": type(result).__name__}
    if text and not text.startswith("<"):
        payload["result"] = text
    for attr in ("GetValue", "Value", "GetValues"):
        try:
            method = getattr(result, attr)
            value = method() if callable(method) else method
            payload["value"] = jsonable(value)
            break
        except Exception:
            continue
    return payload


def as_list(value: Iterable[Any] | None) -> list[Any]:
    if value is None:
        return []
    return list(value)
