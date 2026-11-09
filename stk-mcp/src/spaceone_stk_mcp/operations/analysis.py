"""Access analysis, reports, data providers, lighting and animation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..errors import StkOperationError, StkValidationError, wrap_com_error
from ..stk_common import (
    apply_access_constraint,
    clear_access_constraints,
    compute_access,
    describe_data_providers,
    find_object,
    query_data_provider,
    report_create as build_report,
    truncated_path,
)
from ..timeutil import format_iso, format_stk, parse_time
from ..tooling import object_schema, p, tool


@tool(
    "access_compute",
    "Compute access intervals between two objects over the scenario interval.",
    object_schema(
        {
            "from_object": p("string", "Source object name"),
            "to_object": p("string", "Target object name"),
            "time_step_sec": p("number", "Access computation time step (seconds)"),
        },
        ["from_object", "to_object"],
    ),
    category="access",
    mutating=True,
    returns="access intervals",
    tags=["access", "visibility"],
)
def access_compute(
    session: Any,
    from_object: str,
    to_object: str,
    time_step_sec: float | None = None,
) -> dict[str, Any]:
    source = find_object(session, from_object)
    target = find_object(session, to_object)
    return compute_access(source, target, time_step=time_step_sec)


@tool(
    "access_batch",
    "Compute access from one source object to several target objects.",
    object_schema(
        {
            "from_object": p("string", "Source object name"),
            "to_objects": p("array", "Target names", items={"type": "string"}),
            "time_step_sec": p("number", "Access computation time step (seconds)"),
        },
        ["from_object", "to_objects"],
    ),
    category="access",
    mutating=True,
    returns="per-target access",
)
def access_batch(
    session: Any,
    from_object: str,
    to_objects: list[str],
    time_step_sec: float | None = None,
) -> dict[str, Any]:
    source = find_object(session, from_object)
    results = []
    for name in to_objects:
        try:
            target = find_object(session, name)
            results.append(compute_access(source, target, time_step=time_step_sec))
        except Exception as exc:
            results.append({"to": name, "error": str(exc)})
    return {"from": str(source.InstanceName), "results": results}


@tool(
    "access_report",
    "Generate an STK access report (Access style) between two objects.",
    object_schema(
        {
            "from_object": p("string", "Source object name"),
            "to_object": p("string", "Target object name"),
            "file_path": p("string", "Optional report output path"),
        },
        ["from_object", "to_object"],
    ),
    category="access",
    mutating=True,
    returns="report file",
)
def access_report(
    session: Any, from_object: str, to_object: str, file_path: str | None = None
) -> dict[str, Any]:
    source = find_object(session, from_object)
    target = find_object(session, to_object)
    return build_report(
        session,
        source,
        style="Access",
        file_path=file_path,
        access_object=truncated_path(target),
    )


@tool(
    "access_set_constraint",
    "Set a minimum/maximum access constraint (for example ElevationAngle) on an object.",
    object_schema(
        {
            "object_name": p("string", "Object to constrain"),
            "constraint": p(
                "string",
                "Constraint name",
                enum=[
                    "ElevationAngle",
                    "AzimuthAngle",
                    "Range",
                    "Duration",
                    "BetaAngle",
                    "Altitude",
                    "Lighting",
                    "LineOfSight",
                    "GroundElevationAngle",
                    "SunElevationAngle",
                ],
                default="ElevationAngle",
            ),
            "minimum": p("number", "Minimum value"),
            "maximum": p("number", "Maximum value"),
        },
        ["object_name"],
    ),
    category="access",
    mutating=True,
    returns="constraint configuration",
)
def access_set_constraint(
    session: Any,
    object_name: str,
    constraint: str = "ElevationAngle",
    minimum: float | None = None,
    maximum: float | None = None,
) -> dict[str, Any]:
    obj = find_object(session, object_name)
    return apply_access_constraint(obj, constraint, minimum=minimum, maximum=maximum)


@tool(
    "access_clear_constraints",
    "Remove all access constraints from an object.",
    object_schema({"object_name": p("string", "Object name")}, ["object_name"]),
    category="access",
    mutating=True,
    returns="constraint removal",
)
def access_clear_constraints(session: Any, object_name: str) -> dict[str, Any]:
    return clear_access_constraints(find_object(session, object_name))


@tool(
    "data_provider_list",
    "List data providers and their groups for an object.",
    object_schema({"object_name": p("string", "Object name")}, ["object_name"]),
    category="data",
    returns="data provider list",
)
def data_provider_list(session: Any, object_name: str) -> dict[str, Any]:
    obj = find_object(session, object_name)
    providers = describe_data_providers(obj)
    return {"object": str(obj.InstanceName), "count": len(providers), "providers": providers}


@tool(
    "data_provider_query",
    "Execute a data-provider query and return a table of results. Use a single "
    "time for an instant query or start/stop/step for a time series.",
    object_schema(
        {
            "object_name": p("string", "Object name"),
            "provider": p("string", "Data provider name, e.g. Cartesian Position"),
            "group": p("string", "Group name, e.g. ICRF"),
            "time": p("string", "Single query time"),
            "start_time": p("string", "Series start time"),
            "stop_time": p("string", "Series stop time"),
            "step_sec": p("number", "Series step (seconds)", default=60),
            "max_rows": p("integer", "Maximum rows", default=2000),
        },
        ["object_name", "provider"],
    ),
    category="data",
    returns="data table",
)
def data_provider_query(
    session: Any,
    object_name: str,
    provider: str,
    group: str | None = None,
    time: str | None = None,
    start_time: str | None = None,
    stop_time: str | None = None,
    step_sec: float = 60.0,
    max_rows: int = 2000,
) -> dict[str, Any]:
    obj = find_object(session, object_name)
    return query_data_provider(
        obj,
        provider,
        group,
        time=format_stk(parse_time(time)) if time else None,
        start_time=format_stk(parse_time(start_time)) if start_time else None,
        stop_time=format_stk(parse_time(stop_time)) if stop_time else None,
        step_sec=step_sec,
        max_rows=max_rows,
    )


@tool(
    "lighting_compute",
    "Compute sunlight/eclipse intervals for an object.",
    object_schema(
        {
            "object_name": p("string", "Object name"),
            "group": p("string", "Lighting group", default="Sunlight"),
        },
        ["object_name"],
    ),
    category="analysis",
    mutating=True,
    returns="lighting intervals",
)
def lighting_compute(session: Any, object_name: str, group: str = "Sunlight") -> dict[str, Any]:
    obj = find_object(session, object_name)
    try:
        return query_data_provider(obj, "Lighting Times", group, max_rows=1000)
    except Exception:
        return query_data_provider(obj, "Lighting Times", None, max_rows=1000)


@tool(
    "report_list_styles",
    "List available STK report styles (*.rst) from the installed STKData and the "
    "user's Config\\Styles directories. Use a returned name as report_create.style.",
    object_schema(
        {
            "include_user": p("boolean", "Include the user's Config\\Styles directory", default=True),
            "category": p("string", "Optional category filter, e.g. Access or Satellite"),
            "max_styles": p("integer", "Maximum returned styles", default=500),
        }
    ),
    category="report",
    returns="report style list",
)
def report_list_styles(
    session: Any, include_user: bool = True, category: str | None = None, max_styles: int = 500
) -> dict[str, Any]:
    return _collect_report_styles(
        session, include_user=include_user, category=category, max_styles=max_styles
    )


def _collect_report_styles(
    session: Any,
    *,
    include_user: bool = True,
    category: str | None = None,
    max_styles: int = 500,
) -> dict[str, Any]:
    roots: list[Path] = []
    try:
        app_path = Path(str(session.app.Path))
        roots.append(app_path.parent / "STKData" / "Styles")
    except Exception:
        pass
    if include_user:
        for version in ("STK 11 (x64)", "STK 11", "STK 12"):
            roots.append(Path.home() / "Documents" / version / "Config" / "Styles")
    styles: dict[tuple[str, str], dict[str, Any]] = {}
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.rst"):
            name = path.stem
            category_name = path.parent.name
            if category and category.lower() not in category_name.lower():
                continue
            styles[(category_name, name)] = {
                "name": name,
                "category": category_name,
                "path": str(path),
            }
    rows = sorted(styles.values(), key=lambda item: (item["category"].lower(), item["name"].lower()))
    truncated = len(rows) > max_styles
    return {
        "count": len(rows),
        "styles": rows[:max_styles],
        "truncated": truncated,
        "search_roots": [str(root) for root in roots if root.exists()],
    }


@tool(
    "report_create",
    "Generate an STK report through ReportCreate and return the file path plus preview.",
    object_schema(
        {
            "object_name": p("string", "Object name"),
            "style": p("string", "STK report style, e.g. 'Access' or 'LLA Position'"),
            "file_path": p("string", "Output path (defaults under ~/.spaceone-stk-mcp/reports)"),
            "access_object": p("string", "Optional access target object name"),
            "start_time": p("string", "Report start time"),
            "stop_time": p("string", "Report stop time"),
            "step_sec": p("number", "Report time step"),
            "additional_data": p("string", "STK ReportCreate AdditionalData value"),
            "summary": p("string", "Summary option: Include or Only"),
        },
        ["object_name", "style"],
    ),
    category="report",
    mutating=True,
    returns="report file",
    tags=["report"],
)
def report_create(
    session: Any,
    object_name: str,
    style: str,
    file_path: str | None = None,
    access_object: str | None = None,
    start_time: str | None = None,
    stop_time: str | None = None,
    step_sec: float | None = None,
    additional_data: str | None = None,
    summary: str | None = None,
) -> dict[str, Any]:
    obj = find_object(session, object_name)
    available = _collect_report_styles(session, include_user=True, max_styles=5000)
    class_name = str(obj.ClassName)
    allowed_categories = {class_name.lower(), "access"}
    allowed = [
        item
        for item in available["styles"]
        if str(item["category"]).lower() in allowed_categories
    ]
    if not allowed:
        allowed = list(available["styles"])
    lookup = {str(item["name"]).lower(): str(item["name"]) for item in allowed}
    canonical = lookup.get(style.strip().lower())
    if canonical is None:
        suggestions = [str(item["name"]) for item in allowed][:60]
        raise StkValidationError(
            f"Report style {style!r} is not available for a {class_name}",
            details={
                "object_class": class_name,
                "available_styles": suggestions,
                "style_count": len(allowed),
            },
            hint=f"Call report_list_styles with category={class_name!r} and use an exact "
            "name. For coverage statistics use coverage_stats instead of ReportCreate.",
        )
    style = canonical
    access_path = truncated_path(find_object(session, access_object)) if access_object else None
    try:
        return build_report(
            session,
            obj,
            style=style,
            file_path=file_path,
            access_object=access_path,
            start_time=start_time,
            stop_time=stop_time,
            step_sec=step_sec,
            additional_data=additional_data,
            summary=summary,
        )
    except StkOperationError as exc:
        raise StkOperationError(
            str(exc),
            details=exc.details,
            hint="Verify the style's required time/access data. For coverage use "
            "coverage_stats or data_provider_query.",
        ) from exc


@tool(
    "animation_control",
    "Control scenario animation: play, pause, stop, step, set_time or set_rate.",
    object_schema(
        {
            "action": p(
                "string",
                "Animation action",
                enum=["play", "pause", "stop", "step_forward", "step_backward", "set_time", "set_rate"],
            ),
            "direction": p("string", "Play direction", enum=["forward", "backward"], default="forward"),
            "epoch_seconds": p("number", "Seconds from scenario start for set_time"),
            "time": p("string", "Absolute time for set_time"),
            "high_speed": p("number", "Playback multiplier for set_rate"),
        },
        ["action"],
    ),
    category="animation",
    mutating=True,
    returns="animation state",
)
def animation_control(
    session: Any,
    action: str,
    direction: str = "forward",
    epoch_seconds: float | None = None,
    time: str | None = None,
    high_speed: float | None = None,
) -> dict[str, Any]:
    root = session.root
    sc = session.scenario
    action = (action or "").lower()
    try:
        if action == "play":
            root.PlayBackward() if direction == "backward" else root.PlayForward()
        elif action == "pause":
            root.Pause()
        elif action == "stop":
            root.Rewind()
        elif action == "step_forward":
            root.StepForward()
        elif action == "step_backward":
            root.StepBackward()
        elif action == "set_time":
            if time is not None:
                start = parse_time(str(sc.StartTime))
                seconds = (parse_time(time) - start).total_seconds()
            elif epoch_seconds is not None:
                seconds = float(epoch_seconds)
            else:
                raise StkValidationError("set_time requires time or epoch_seconds")
            root.CurrentTime = float(seconds)
        elif action == "set_rate":
            if high_speed is None:
                raise StkValidationError("set_rate requires high_speed")
            root.HighSpeed = float(high_speed)
        else:
            raise StkValidationError(f"Unknown animation action: {action!r}")
    except StkValidationError:
        raise
    except Exception as exc:
        raise wrap_com_error(exc, f"Animation action {action}") from exc
    return animation_info(session)


@tool(
    "animation_info",
    "Read the current animation time, scenario time bounds and playback rate.",
    object_schema({}),
    category="animation",
    returns="animation state",
)
def animation_info(session: Any) -> dict[str, Any]:
    root = session.root
    sc = session.scenario
    start = parse_time(str(sc.StartTime))
    current_seconds = None
    current_iso = None
    try:
        from datetime import timedelta

        current_seconds = float(root.CurrentTime)
        current_iso = format_iso(start + timedelta(seconds=current_seconds))
    except Exception:
        pass
    high_speed = None
    try:
        high_speed = float(root.HighSpeed)
    except Exception:
        pass
    return {
        "scenario": str(sc.InstanceName),
        "current_time_sec": current_seconds,
        "current_time_iso": current_iso,
        "scenario_start": str(sc.StartTime),
        "scenario_stop": str(sc.StopTime),
        "high_speed": high_speed,
    }


@tool(
    "scenario_set_view",
    "Activate the 2D/3D graphics windows and optionally show all objects.",
    object_schema(
        {
            "show_3d": p("boolean", "Activate the 3D window", default=True),
            "show_2d": p("boolean", "Activate the 2D window", default=False),
            "maximize": p("boolean", "Maximize the activated window", default=False),
        }
    ),
    category="animation",
    mutating=True,
    returns="window state",
)
def scenario_set_view(
    session: Any, show_3d: bool = True, show_2d: bool = False, maximize: bool = False
) -> dict[str, Any]:
    activated: list[str] = []
    try:
        windows = session.app.Windows
        for index in range(int(windows.Count)):
            window = windows.Item(index)
            caption = str(window.Caption)
            if (show_3d and "3D" in caption) or (show_2d and "2D" in caption):
                window.Activate()
                if maximize:
                    window.WindowState = 3
                activated.append(caption)
    except Exception as exc:
        raise wrap_com_error(exc, "Activating graphics windows") from exc
    return {"activated": activated, "show_3d": show_3d, "show_2d": show_2d}
