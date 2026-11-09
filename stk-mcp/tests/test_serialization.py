from __future__ import annotations

from spaceone_stk_mcp.serialization import access_intervals, dataset_table, jsonable, parse_scalar


def test_parse_scalar_numbers_and_times():
    assert parse_scalar("42") == 42
    assert parse_scalar("3.5") == 3.5
    assert parse_scalar("1 Jan 2026 00:00:00.000") == "1 Jan 2026 00:00:00.000"
    assert parse_scalar(None) is None
    assert parse_scalar(float("nan")) is None


def test_jsonable_nested():
    value = {"a": (1, 2), "b": [float("inf"), "x"]}
    assert jsonable(value) == {"a": [1, 2], "b": [None, "x"]}


class _DataSets:
    Count = 2

    def Item(self, index):
        return _DataSet(index)


class _DataSet:
    def __init__(self, index):
        self.ElementName = "Time" if index == 0 else "x"

    def GetValues(self):
        return ("1 Jan 2026 00:00:00.000",) if self.ElementName == "Time" else (7000.0,)


class _Result:
    DataSets = _DataSets()


def test_dataset_table():
    table = dataset_table(_Result())
    assert table["columns"] == ["Time", "x"]
    assert table["rows"][0]["x"] == 7000.0


class _Collection:
    Count = 1

    def GetInterval(self, index):
        return ("1 Jan 2026 00:00:00.000", "1 Jan 2026 00:10:00.000")


class _Access:
    ComputedAccessIntervalTimes = _Collection()


def test_access_intervals():
    intervals = access_intervals(_Access())
    assert len(intervals) == 1
    assert intervals[0]["duration_sec"] == 600.0
