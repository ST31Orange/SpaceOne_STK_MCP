from __future__ import annotations

from pathlib import Path

import pytest

from spaceone_stk_mcp.errors import StkValidationError
from spaceone_stk_mcp.operations.scenario import (
    _check_save_size,
    _ensure_safe_scenario_dir,
    _validate_ascii_path,
)
from spaceone_stk_mcp.stk_common import validate_name


def test_validate_name_accepts_chinese_and_spaces():
    assert validate_name("北京地面站") == "北京地面站"
    assert validate_name("Sat 1") == "Sat 1"


@pytest.mark.parametrize("value", ["", "  ", "a/b", "a\\b", "bad\x00name"])
def test_validate_name_rejects_paths_and_control(value):
    with pytest.raises(StkValidationError):
        validate_name(value)


def test_save_path_rejects_chinese():
    with pytest.raises(StkValidationError):
        _validate_ascii_path(Path(r"C:\场景\mission.sc"))


def test_save_path_accepts_ascii():
    assert _validate_ascii_path(Path(r"C:\STK\mission.sc"))


def test_save_directory_refuses_unrelated_files(tmp_path):
    (tmp_path / "other_scenario.sc").write_text("x", encoding="utf-8")
    with pytest.raises(StkValidationError) as exc:
        _ensure_safe_scenario_dir(tmp_path / "mission.sc")
    assert exc.value.code == "UNSAFE_SAVE_DIRECTORY"


def test_save_directory_allows_scenario_artifacts(tmp_path):
    (tmp_path / "mission.sc").write_text("x", encoding="utf-8")
    (tmp_path / "Catalog").mkdir()
    (tmp_path / "mission.sc3").write_text("x", encoding="utf-8")
    _ensure_safe_scenario_dir(tmp_path / "mission.sc")


def test_save_size_limit(tmp_path):
    (tmp_path / "mission.sc").write_bytes(b"x" * 2048)

    class _Settings:
        max_save_bytes = 1024

    class _Session:
        settings = _Settings()

    with pytest.raises(StkValidationError) as exc:
        _check_save_size(_Session(), tmp_path / "mission.sc")
    assert exc.value.code == "SAVE_TOO_LARGE"
