"""Object-model helpers shared by the operation modules."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .enums import OBJECT_TYPE
from .errors import StkNotFoundError, StkOperationError, StkValidationError, wrap_com_error
from .serialization import access_intervals, dataset_table
from .timeutil import format_iso, format_stk, parse_time, resolve_interval

def validate_name(name: str, label: str = "name") -> str:
    text = (name or "").strip()
    if not text:
        raise StkValidationError(f"{label} must not be empty")
    if len(text) > 128:
        raise StkValidationError(f"{label} must be at most 128 characters")
    if "/" in text or "\\" in text or any(ord(char) < 32 for char in text):
        raise StkValidationError(
            f"{label} contains unsupported characters: {name!r}",
            hint="Do not use path separators or control characters.",
        )
    return text


def child_list(obj: Any) -> list[Any]:
    children = getattr(obj, "Children", None)
    if children is None:
        return []
    result = []
    for i in range(int(children.Count)):
        try:
            result.append(children.Item(i))
        except Exception:
            continue
    return result


def find_child(parent: Any, name: str) -> Any:
    children = getattr(parent, "Children", None)
    if children is None:
        raise StkNotFoundError(f"Object '{name}' has no children")
    try:
        return children.Item(name)
    except Exception:
        pass
    for child in child_list(parent):
        try:
            if str(child.InstanceName).lower() == name.lower():
                return child
        except Exception:
            continue
    raise StkNotFoundError(f"Child object '{name}' was not found under {getattr(parent, 'Path', parent)}")


def find_object(session: Any, name_or_path: str) -> Any:
    """Resolve an object by name, truncated path or full STK path."""
    text = (name_or_path or "").strip()
    if not text:
        raise StkValidationError("object name must not be empty")
    root = session.root
    scenario = session.scenario
    if text.startswith("/"):
        text = text[1:]
    if "/" in text:
        for candidate in (text, text.replace("Application/STK/", "")):
            try:
                return root.GetObjectFromPath(candidate)
            except Exception:
                continue
    try:
        return scenario.Children.Item(text)
    except Exception:
        pass
    lowered = text.lower()
    for child in child_list(scenario):
        try:
            if str(child.InstanceName).lower() == lowered:
                return child
        except Exception:
            continue
    # Search nested objects (sensors, equipment, ...).
    stack = child_list(scenario)
    while stack:
        obj = stack.pop()
        try:
            if str(obj.InstanceName).lower() == lowered:
                return obj
        except Exception:
            pass
        stack.extend(child_list(obj))
    raise StkNotFoundError(
        f"Object '{name_or_path}' was not found in scenario '{scenario.InstanceName}'"
    )


def truncated_path(obj: Any) -> str:
    """Return a Connect-style path such as ``*/Satellite/Sat1``."""
    try:
        path = str(obj.Path)
    except Exception:
        path = ""
    marker = "/Scenario/"
    if marker in path:
        tail = path.split(marker, 1)[1]
        parts = tail.split("/")
        if parts:
            parts = parts[1:]  # drop the scenario name
            return "*/" + "/".join(parts)
    class_name = str(getattr(obj, "ClassName", ""))
    instance = str(getattr(obj, "InstanceName", ""))
    if class_name and instance:
        return f"*/{class_name}/{instance}"
    return path


def object_summary(obj: Any, *, children: bool = False) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for attr, key in (
        ("InstanceName", "name"),
        ("ClassName", "class_name"),
        ("Path", "path"),
        ("ShortDescription", "short_description"),
        ("LongDescription", "long_description"),
    ):
        try:
            payload[key] = str(getattr(obj, attr))
        except Exception:
            continue
    try:
        payload["class_type"] = int(obj.ClassType)
    except Exception:
        pass
    if children:
        payload["children"] = [object_summary(child) for child in child_list(obj)]
    return payload


def scenario_info(session: Any) -> dict[str, Any]:
    sc = session.scenario
    start = parse_time(str(sc.StartTime))
    stop = parse_time(str(sc.StopTime))
    info = {
        "name": str(sc.InstanceName),
        "path": str(getattr(sc, "Path", "")),
        "start_time": format_stk(start),
        "stop_time": format_stk(stop),
        "start_iso": format_iso(start),
        "stop_iso": format_iso(stop),
        "duration_sec": (stop - start).total_seconds(),
        "epoch": str(getattr(sc, "Epoch", "")),
        "object_count": int(sc.Children.Count),
        "objects": [object_summary(child) for child in child_list(sc)],
    }
    return info


def new_object(sc: Any, type_name: str, name: str, *, replace: bool = False) -> Any:
    if type_name not in OBJECT_TYPE:
        raise StkValidationError(f"Unsupported object type: {type_name}")
    instance = validate_name(name, "object name")
    existing = None
    try:
        existing = sc.Children.Item(instance)
    except Exception:
        existing = None
    if existing is not None:
        if not replace:
            raise StkOperationError(
                f"Object '{instance}' already exists in the scenario",
                hint="Choose another name or pass replace_existing=true.",
            )
        try:
            existing.Unload()
        except Exception as exc:
            raise wrap_com_error(exc, f"Unloading existing '{instance}'") from exc
    try:
        return sc.Children.New(OBJECT_TYPE[type_name], instance)
    except Exception as exc:
        raise wrap_com_error(exc, f"Creating {type_name} '{instance}'") from exc


def assign_geodetic(obj: Any, latitude_deg: float, longitude_deg: float, altitude_km: float = 0.0) -> None:
    if not -90.0 <= latitude_deg <= 90.0:
        raise StkValidationError("latitude_deg must be between -90 and 90")
    if not -180.0 <= longitude_deg <= 180.0:
        raise StkValidationError("longitude_deg must be between -180 and 180")
    try:
        obj.Position.AssignGeodetic(float(latitude_deg), float(longitude_deg), float(altitude_km))
    except Exception as exc:
        raise wrap_com_error(exc, "AssignGeodetic") from exc


def get_geodetic(obj: Any, time: str | None = None) -> dict[str, Any]:
    """Read a ground object's geodetic position via its LLA data provider."""
    providers = ["LLA State", "LLA Position", "Cartesian Position"]
    for provider in providers:
        try:
            dp = obj.DataProviders.Item(provider)
        except Exception:
            continue
        group_names: list[str] = []
        try:
            group_names = [str(dp.Group.Item(i).Name) for i in range(dp.Group.Count)]
        except Exception:
            pass
        for group_name in group_names or ["Geodetic", "Fixed", "ICRF"]:
            try:
                group = dp.Group.Item(group_name)
                if time:
                    result = group.ExecSingle(time)
                else:
                    result = group.ExecSingle(getattr(obj.Root.CurrentScenario, "StartTime"))
                return {
                    "object": str(obj.InstanceName),
                    "provider": provider,
                    "group": group_name,
                    **dataset_table(result),
                }
            except Exception:
                continue
    raise StkOperationError(f"No geodetic data provider is available for {obj.InstanceName}")


def query_data_provider(
    obj: Any,
    provider_name: str,
    group_name: str | None = None,
    *,
    start_time: str | None = None,
    stop_time: str | None = None,
    step_sec: float | None = None,
    time: str | None = None,
    elements: list[str] | None = None,
    max_rows: int = 20000,
) -> dict[str, Any]:
    try:
        dp = obj.DataProviders.Item(provider_name)
    except Exception as exc:
        raise StkNotFoundError(
            f"Data provider '{provider_name}' is not available on {obj.InstanceName}",
            details={"object": str(obj.InstanceName)},
        ) from exc

    groups: list[str] = []
    group_holder: Any = None
    try:
        group_holder = dp.Group
        groups = [str(group_holder.Item(i).Name) for i in range(int(group_holder.Count))]
    except Exception:
        groups = []
        group_holder = None

    if group_name:
        if groups and group_name not in groups:
            raise StkValidationError(
                f"Group '{group_name}' is not available for '{provider_name}'",
                details={"available_groups": groups},
            )
        if group_holder is None:
            raise StkValidationError(
                f"Provider '{provider_name}' does not expose groups",
                details={"requested_group": group_name},
            )
        group = group_holder.Item(group_name)
    elif groups:
        group = group_holder.Item(groups[0])
        group_name = groups[0]
    elif group_holder is not None:
        group = group_holder
        group_name = None
    else:
        # Coverage and a few analysis providers expose Exec directly on the
        # data-provider object rather than through a Group collection.
        group = dp
        group_name = None

    scenario = obj.Root.CurrentScenario
    start = start_time or str(scenario.StartTime)
    stop = stop_time or str(scenario.StopTime)
    step = float(step_sec if step_sec is not None else 60.0)
    attempts: list[Any] = []
    if time is not None:
        attempts = [
            lambda: group.ExecSingle(time),
            lambda: group.Exec(time, time, 1),
            lambda: group.Exec(time, time),
            lambda: group.Exec(),
        ]
    else:
        attempts = [
            lambda: group.Exec(start, stop, step),
            lambda: group.Exec(start, stop),
            lambda: group.Exec(),
            lambda: group.ExecSingle(start),
        ]
    result = None
    last_error: Exception | None = None
    for attempt in attempts:
        try:
            result = attempt()
            break
        except Exception as exc:
            last_error = exc
            continue
    if result is None:
        raise StkOperationError(
            f"Could not execute data provider '{provider_name}': {last_error}",
            details={"object": str(obj.InstanceName)},
        )
    table = dataset_table(result, max_rows=max_rows)
    return {
        "object": str(obj.InstanceName),
        "provider": provider_name,
        "group": group_name,
        "available_groups": groups,
        **table,
    }


def get_access(from_obj: Any, to_obj: Any) -> Any:
    try:
        return from_obj.GetAccessToObject(to_obj)
    except Exception as exc:
        raise wrap_com_error(
            exc, f"GetAccessToObject({from_obj.InstanceName} -> {to_obj.InstanceName})"
        ) from exc


def compute_access(from_obj: Any, to_obj: Any, *, time_step: float | None = None) -> dict[str, Any]:
    access = get_access(from_obj, to_obj)
    if time_step is not None:
        try:
            access.TimeStep = float(time_step)
        except Exception:
            pass
    try:
        access.ComputeAccess()
    except Exception as exc:
        raise wrap_com_error(exc, "ComputeAccess") from exc
    intervals = access_intervals(access)
    return {
        "from": str(from_obj.InstanceName),
        "to": str(to_obj.InstanceName),
        "access_count": len(intervals),
        "total_duration_sec": sum(float(item.get("duration_sec", 0.0)) for item in intervals),
        "intervals": intervals,
    }


def apply_access_constraint(
    obj: Any, constraint: str, *, minimum: float | None = None, maximum: float | None = None
) -> dict[str, Any]:
    from .enums import access_constraint_code

    code = access_constraint_code(constraint)
    try:
        collection = obj.AccessConstraints
    except Exception as exc:
        raise StkOperationError(
            f"{obj.InstanceName} does not expose access constraints: {exc}"
        ) from exc
    try:
        active = bool(collection.IsConstraintActive(code))
    except Exception:
        active = False
    try:
        constraint_obj = collection.GetActiveConstraint(code) if active else collection.AddConstraint(code)
        if minimum is not None and hasattr(constraint_obj, "EnableMin"):
            constraint_obj.EnableMin = True
            constraint_obj.Min = float(minimum)
        if maximum is not None and hasattr(constraint_obj, "EnableMax"):
            constraint_obj.EnableMax = True
            constraint_obj.Max = float(maximum)
        return {
            "object": str(obj.InstanceName),
            "constraint": constraint,
            "constraint_code": code,
            "minimum": minimum,
            "maximum": maximum,
        }
    except Exception as exc:
        raise wrap_com_error(exc, f"Setting {constraint} constraint") from exc


def clear_access_constraints(obj: Any) -> dict[str, Any]:
    collection = obj.AccessConstraints
    removed: list[int] = []
    try:
        codes = []
        for i in range(int(collection.Count)):
            try:
                codes.append(int(collection.Item(i).ConstraintType))
            except Exception:
                try:
                    codes.append(int(collection.Item(i).Type))
                except Exception:
                    continue
        for code in codes:
            try:
                collection.RemoveConstraint(code)
                removed.append(code)
            except Exception:
                continue
    except Exception as exc:
        raise wrap_com_error(exc, "Clearing access constraints") from exc
    return {"object": str(obj.InstanceName), "removed_constraints": removed}


def report_create(
    session: Any,
    obj: Any,
    *,
    style: str,
    file_path: str | None = None,
    access_object: str | None = None,
    start_time: str | None = None,
    stop_time: str | None = None,
    step_sec: float | None = None,
    summary: str | None = None,
    additional_data: str | None = None,
    report_type: str = "Save",
) -> dict[str, Any]:
    """Generate a report through the modern ``ReportCreate`` Connect command."""
    session.settings.ensure_dirs()
    if file_path:
        path = Path(file_path).expanduser()
        if not path.is_absolute():
            path = session.settings.data_dir / "reports" / path
    else:
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", f"{obj.InstanceName}_{style}")
        path = session.settings.data_dir / "reports" / f"{safe}.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == "":
        path = path.with_suffix(".txt")

    command = f'ReportCreate {truncated_path(obj)} Type {report_type} Style "{style}" File "{path}"'
    if access_object:
        command += f" AccessObject {access_object}"
    if start_time and stop_time:
        command += f' TimePeriod "{format_stk(parse_time(start_time))}" "{format_stk(parse_time(stop_time))}"'
        if step_sec:
            command += f" TimeStep {float(step_sec)}"
    if additional_data:
        command += f' AdditionalData "{additional_data}"'
    if summary:
        command += f" Summary {summary}"

    try:
        session.root.ExecuteCommand(command)
    except Exception as exc:
        raise wrap_com_error(exc, f"ReportCreate({style})") from exc
    exists = path.exists()
    preview = ""
    if exists:
        try:
            preview = path.read_text(encoding="utf-8", errors="replace")[:4000]
        except Exception:
            preview = ""
    return {
        "object": str(obj.InstanceName),
        "style": style,
        "command": command,
        "file_path": str(path),
        "exists": exists,
        "size": path.stat().st_size if exists else 0,
        "preview": preview,
    }


def describe_data_providers(obj: Any) -> list[dict[str, Any]]:
    result = []
    providers = obj.DataProviders
    for i in range(int(providers.Count)):
        try:
            dp = providers.Item(i)
            name = str(dp.Name)
        except Exception:
            continue
        groups: list[str] = []
        try:
            groups = [str(dp.Group.Item(j).Name) for j in range(dp.Group.Count)]
        except Exception:
            pass
        result.append({"name": name, "groups": groups})
    return result


def resolve_scenario_interval(session: Any, start_time: str | None, stop_time: str | None, duration_hours: float | None = None) -> tuple[Any, Any]:
    sc = session.scenario
    default_start = parse_time(str(sc.StartTime))
    return resolve_interval(
        start_time,
        stop_time,
        default_start=default_start,
        duration_hours=duration_hours if duration_hours is not None else session.settings.default_duration_hours,
    )


def write_csv(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    import csv

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
