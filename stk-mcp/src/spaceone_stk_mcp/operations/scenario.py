"""Scenario lifecycle operations."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from ..errors import StkOperationError, StkValidationError, wrap_com_error
from ..stk_common import scenario_info, validate_name
from ..timeutil import (
    UTC,
    format_iso,
    format_stk,
    parse_time,
    resolve_interval,
)
from ..tooling import object_schema, p, tool


def _scenario_path(sc: Any) -> str:
    for attr in ("Path", "ScenarioPath", "FilePath"):
        try:
            value = str(getattr(sc, attr))
            if value and value.startswith(("C:", "D:", "\\\\", "/")):
                return value
        except Exception:
            continue
    return ""


def _stored_path(session: Any) -> str | None:
    value = session._conversation_state.get("scenario_path")
    return str(value) if value else None


def _store_path(session: Any, path: str | None) -> None:
    session._conversation_state["scenario_path"] = str(path) if path else None


def _default_scenario_path(session: Any) -> Path:
    version = str(session.version or "")
    major = "12" if "12" in version else "11"
    folder = "STK 12" if major == "12" else "STK 11 (x64)"
    base = Path.home() / "Documents" / folder
    name = str(session.scenario.InstanceName)
    return _validate_ascii_path(base / name / f"{name}.sc")


def _is_scenario_artifact(target: Path, entry: Path) -> bool:
    """True for files/folders STK itself writes next to a scenario .sc file."""
    name = entry.name
    if name == target.name:
        return True
    if entry.is_dir() and name.lower() == "catalog":
        return True
    if name.startswith(target.stem + "."):
        return True
    if name == target.stem + "TimelinePrefs.xml":
        return True
    return False


def _ensure_safe_scenario_dir(target: Path) -> None:
    """Refuse to save into a directory that holds unrelated files.

    STK's SaveScenarioAs writes a bag of sidecar files. Pointing it at an
    existing directory (for example the STK user directory, or a folder with
    other scenarios) can merge unrelated content into the scenario folder. We
    only allow a new/empty folder, or a folder that already contains this
    scenario's own artifacts.
    """
    parent = target.parent
    if not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)
        return
    unrelated = [
        entry.name for entry in parent.iterdir() if not _is_scenario_artifact(target, entry)
    ]
    if unrelated:
        raise StkValidationError(
            f"Refusing to save into a directory with unrelated files: {parent}",
            code="UNSAFE_SAVE_DIRECTORY",
            details={"directory": str(parent), "unrelated": unrelated[:20]},
            hint="Use a new empty folder, e.g. C:\\STK\\scenarios\\mission\\mission.sc, "
            "or remove the unrelated files first.",
        )


def _scenario_folder_size(target: Path) -> int:
    parent = target.parent
    if not parent.exists():
        return 0
    total = 0
    for path in parent.rglob("*"):
        try:
            if path.is_file():
                total += path.stat().st_size
        except OSError:
            continue
    return total


def _check_save_size(session: Any, target: Path) -> None:
    size = _scenario_folder_size(target)
    limit = int(getattr(session.settings, "max_save_bytes", 2_000_000_000))
    if size > limit:
        raise StkValidationError(
            f"Scenario folder is {size} bytes, above the safety limit of {limit}",
            code="SAVE_TOO_LARGE",
            details={"path": str(target), "size_bytes": size, "limit_bytes": limit},
            hint="Do not save this folder. Check for unrelated large files; use a fresh "
            "empty scenario folder and increase STK_MCP_MAX_SAVE_BYTES only if intentional.",
        )


@tool(
    "scenario_create",
    "Create a new STK scenario. Closes the open scenario only when "
    "replace_existing=true; otherwise it fails rather than silently discarding work.",
    object_schema(
        {
            "name": p("string", "Scenario name"),
            "start_time": p(
                "string",
                "Start epoch (ISO-8601 or STK UTCG). Defaults to the current UTC minute.",
            ),
            "stop_time": p("string", "Stop epoch (ISO-8601 or STK UTCG)"),
            "duration_hours": p(
                "number", "Duration used when stop_time is omitted", default=24.0
            ),
            "description": p("string", "Optional scenario description"),
            "path": p(
                "string",
                "Optional .sc path. Saving requires confirm_save=true and an ASCII-only path.",
            ),
            "confirm_save": p(
                "boolean",
                "Explicit user approval to save; never set true without asking the user",
                default=False,
            ),
            "replace_existing": p(
                "boolean", "Close an already-open scenario first", default=False
            ),
        },
        ["name"],
    ),
    category="scenario",
    mutating=True,
    returns="scenario info",
    tags=["scenario", "create"],
)
def scenario_create(
    session: Any,
    name: str,
    start_time: str | None = None,
    stop_time: str | None = None,
    duration_hours: float | None = None,
    description: str | None = None,
    path: str | None = None,
    confirm_save: bool = False,
    replace_existing: bool = False,
) -> dict[str, Any]:
    name = validate_name(name, "scenario name")
    root = session.root
    current = root.CurrentScenario
    if current is not None:
        if not replace_existing:
            raise StkOperationError(
                f"A scenario is already open: {current.InstanceName}",
                hint="Call scenario_close first or pass replace_existing=true.",
            )
        try:
            root.CloseScenario()
        except Exception as exc:
            raise wrap_com_error(exc, "Closing the current scenario") from exc

    now = datetime.now(UTC).replace(second=0, microsecond=0)
    start, stop = resolve_interval(
        start_time,
        stop_time,
        default_start=now,
        duration_hours=duration_hours if duration_hours is not None else session.settings.default_duration_hours,
    )
    try:
        root.NewScenario(name)
        sc = root.CurrentScenario
        if sc is None:
            raise StkOperationError("STK did not create the scenario")
        _store_path(session, None)
        sc.SetTimePeriod(format_stk(start), format_stk(stop))
        if description:
            for attr in ("Description", "ShortDescription", "LongDescription"):
                try:
                    setattr(sc, attr, description)
                    break
                except Exception:
                    continue
    except Exception as exc:
        raise wrap_com_error(exc, f"Creating scenario '{name}'") from exc

    saved_path = None
    if path:
        if not confirm_save:
            raise StkValidationError(
                "Saving a scenario requires explicit user confirmation",
                code="SAVE_CONFIRMATION_REQUIRED",
                hint="Ask the user for an ASCII-only path and permission, then call "
                "scenario_save with confirm_save=true.",
            )
        saved_path = _save_scenario(session, path)
    info = scenario_info(session)
    if saved_path:
        info["saved_path"] = saved_path
    applied = False
    if description:
        for attr in ("Description", "ShortDescription", "LongDescription"):
            try:
                setattr(sc, attr, description)
                applied = True
                break
            except Exception:
                continue
    info["description"] = description if applied else None
    info["description_applied"] = applied
    return info


def _validate_ascii_path(path: Path) -> Path:
    if not str(path).isascii():
        raise StkValidationError(
            f"Scenario save path must be ASCII-only (no Chinese characters): {path}",
            hint="Choose a path such as C:\\STK\\scenarios\\mission.sc.",
        )
    return path


def _save_scenario(session: Any, path: str) -> str:
    target = Path(path).expanduser()
    if not target.is_absolute():
        target = session.settings.data_dir / target
    if target.suffix.lower() != ".sc":
        target = target.with_suffix(".sc")
    _validate_ascii_path(target)
    _ensure_safe_scenario_dir(target)
    _check_save_size(session, target)
    try:
        session.root.SaveScenarioAs(str(target))
    except Exception as exc:
        raise wrap_com_error(exc, f"Saving scenario as '{target}'") from exc
    _check_save_size(session, target)
    _store_path(session, str(target))
    return str(target)


@tool(
    "scenario_open",
    "Open an existing .sc scenario file.",
    object_schema(
        {
            "path": p("string", "Absolute or relative path to a .sc file"),
            "replace_existing": p(
                "boolean", "Close an already-open scenario first", default=True
            ),
        },
        ["path"],
    ),
    category="scenario",
    mutating=True,
    returns="scenario info",
)
def scenario_open(
    session: Any, path: str, replace_existing: bool = True
) -> dict[str, Any]:
    target = Path(path).expanduser()
    if not target.is_absolute():
        target = (Path.cwd() / target).resolve()
    if not target.exists():
        raise StkOperationError(f"Scenario file not found: {target}")
    root = session.root
    if root.CurrentScenario is not None:
        if not replace_existing:
            raise StkOperationError("A scenario is already open")
        root.CloseScenario()
    try:
        root.LoadScenario(str(target))
    except Exception as exc:
        raise wrap_com_error(exc, f"Loading scenario '{target}'") from exc
    _store_path(session, str(target))
    info = scenario_info(session)
    info["loaded_path"] = str(target)
    return info


@tool(
    "scenario_save",
    "Save the current scenario in place or to a new .sc path. Requires explicit "
    "confirm_save=true; without a path it uses STK's default scenario location. "
    "Paths must be ASCII-only (no Chinese characters).",
    object_schema(
        {
            "path": p("string", "Save-as path; omit to save in STK's default location"),
            "confirm_save": p(
                "boolean",
                "Explicit user approval to save; never set true without asking the user",
                default=False,
            ),
            "overwrite": p("boolean", "Allow replacing an existing save-as file", default=True),
        }
    ),
    category="scenario",
    mutating=True,
    returns="save result",
)
def scenario_save(
    session: Any,
    path: str | None = None,
    confirm_save: bool = False,
    overwrite: bool = True,
) -> dict[str, Any]:
    if not confirm_save:
        raise StkValidationError(
            "Saving a scenario requires explicit user confirmation",
            code="SAVE_CONFIRMATION_REQUIRED",
            hint="Ask the user for permission and an ASCII-only path, then call "
            "scenario_save with confirm_save=true.",
        )
    if path:
        target = Path(path).expanduser()
        if not target.is_absolute():
            target = session.settings.data_dir / target
        if target.suffix.lower() != ".sc":
            target = target.with_suffix(".sc")
        _validate_ascii_path(target)
        if target.exists() and not overwrite:
            raise StkValidationError(f"Refusing to overwrite {target}")
        saved = _save_scenario(session, str(target))
        return {
            "status": "saved",
            "path": saved,
            "name": str(session.scenario.InstanceName),
            "confirmed": True,
        }
    existing = _stored_path(session)
    if existing and Path(existing).exists():
        _validate_ascii_path(Path(existing))
        _ensure_safe_scenario_dir(Path(existing))
        _check_save_size(session, Path(existing))
        try:
            session.root.SaveScenario()
        except Exception as exc:
            raise wrap_com_error(exc, f"Saving scenario in place '{existing}'") from exc
        _check_save_size(session, Path(existing))
        return {
            "status": "saved",
            "path": existing,
            "name": str(session.scenario.InstanceName),
            "confirmed": True,
            "used_default_location": False,
        }
    target = _default_scenario_path(session)
    saved = _save_scenario(session, str(target))
    return {
        "status": "saved",
        "path": saved,
        "name": str(session.scenario.InstanceName),
        "confirmed": True,
        "used_default_location": True,
    }


@tool(
    "scenario_close",
    "Close the current scenario without quitting STK.",
    object_schema({}),
    category="scenario",
    mutating=True,
    returns="close result",
)
def scenario_close(session: Any) -> dict[str, Any]:
    current = session.scenario
    name = str(current.InstanceName)
    try:
        session.root.CloseScenario()
    except Exception as exc:
        raise wrap_com_error(exc, "CloseScenario") from exc
    _store_path(session, None)
    return {"status": "closed", "scenario": name}


@tool(
    "scenario_info",
    "Return the current scenario name, time period, duration and top-level objects.",
    object_schema({}),
    category="scenario",
    returns="scenario info",
)
def scenario_info_tool(session: Any) -> dict[str, Any]:
    return scenario_info(session)


@tool(
    "scenario_set_time",
    "Update the scenario start/stop time (or extend by duration_hours).",
    object_schema(
        {
            "start_time": p("string", "New start epoch"),
            "stop_time": p("string", "New stop epoch"),
            "duration_hours": p("number", "Duration from start when stop is omitted"),
        }
    ),
    category="scenario",
    mutating=True,
    returns="scenario time",
)
def scenario_set_time(
    session: Any,
    start_time: str | None = None,
    stop_time: str | None = None,
    duration_hours: float | None = None,
) -> dict[str, Any]:
    sc = session.scenario
    current_start = parse_time(str(sc.StartTime))
    current_stop = parse_time(str(sc.StopTime))
    start = parse_time(start_time, default=current_start) if start_time else current_start
    if stop_time:
        stop = parse_time(stop_time)
    elif duration_hours is not None:
        stop = start + timedelta(hours=duration_hours)
    else:
        stop = current_stop
    if stop <= start:
        raise StkValidationError("stop_time must be later than start_time")
    try:
        sc.SetTimePeriod(format_stk(start), format_stk(stop))
    except Exception as exc:
        raise wrap_com_error(exc, "SetTimePeriod") from exc
    return {
        "start_time": format_stk(start),
        "stop_time": format_stk(stop),
        "start_iso": format_iso(start),
        "stop_iso": format_iso(stop),
        "duration_sec": (stop - start).total_seconds(),
    }
