"""Satellite creation, orbit definition, propagation and state queries."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..enums import (
    CLASSICAL_COORDINATE_SYSTEM,
    normalize_propagator,
    propagator_code,
)
from ..errors import (
    StkOperationError,
    StkValidationError,
    wrap_com_error,
)
from ..stk_common import (
    find_object,
    new_object,
    object_summary,
    query_data_provider,
    validate_name,
    write_csv,
)
from ..timeutil import format_stk, parse_time, resolve_interval
from ..tooling import object_schema, p, tool


def _satellite(session: Any, name: str) -> Any:
    obj = find_object(session, name)
    if str(getattr(obj, "ClassName", "")) != "Satellite":
        raise StkValidationError(f"Object '{name}' is a {obj.ClassName}, not a Satellite")
    return obj


def _propagate(sat: Any) -> None:
    try:
        sat.Propagator.Propagate()
    except Exception as exc:
        raise wrap_com_error(exc, f"Propagating {sat.InstanceName}") from exc


def _coordinate_code(value: str | None) -> int:
    if not value:
        return CLASSICAL_COORDINATE_SYSTEM["J2000"]
    for key, code in CLASSICAL_COORDINATE_SYSTEM.items():
        if key.lower() == str(value).lower():
            return code
    raise StkValidationError(
        f"Unsupported coordinate system: {value!r}",
        details={"allowed": sorted(CLASSICAL_COORDINATE_SYSTEM)},
    )


@tool(
    "satellite_create",
    "Create a satellite in the current scenario and select a propagator.",
    object_schema(
        {
            "name": p("string", "Satellite name"),
            "propagator": p(
                "string",
                "Propagator type",
                enum=[
                    "TwoBody",
                    "J2Perturbation",
                    "J4Perturbation",
                    "HPOP",
                    "SGP4",
                    "Astrogator",
                    "StkExternal",
                ],
                default="TwoBody",
            ),
            "replace_existing": p(
                "boolean", "Unload an existing satellite with the same name", default=False
            ),
        },
        ["name"],
    ),
    category="satellite",
    mutating=True,
    returns="satellite summary",
    tags=["satellite", "create"],
)
def satellite_create(
    session: Any,
    name: str,
    propagator: str = "TwoBody",
    replace_existing: bool = False,
) -> dict[str, Any]:
    name = validate_name(name, "satellite name")
    sc = session.scenario
    sat = new_object(sc, "Satellite", name, replace=replace_existing)
    prop_name = normalize_propagator(propagator)
    try:
        sat.SetPropagatorType(propagator_code(prop_name))
    except Exception as exc:
        raise wrap_com_error(exc, "SetPropagatorType") from exc
    return {
        **object_summary(sat),
        "propagator": prop_name,
        "propagator_code": propagator_code(prop_name),
    }


@tool(
    "satellite_set_orbit",
    "Define a satellite orbit from classical elements, a Cartesian state, TLE "
    "lines, or an ephemeris file, then propagate it.",
    object_schema(
        {
            "satellite_name": p("string", "Satellite name"),
            "mode": p(
                "string",
                "Orbit representation",
                enum=["classical", "cartesian", "tle", "from_file"],
                default="classical",
            ),
            "semi_major_axis_km": p("number", "Classical: semi-major axis (km)", minimum=1),
            "eccentricity": p("number", "Classical: eccentricity (0-1)", minimum=0, maximum=0.999999),
            "inclination_deg": p("number", "Classical: inclination (deg)", minimum=0, maximum=180),
            "raan_deg": p("number", "Classical: right ascension of ascending node (deg)"),
            "arg_of_perigee_deg": p("number", "Classical: argument of perigee (deg)"),
            "mean_anomaly_deg": p("number", "Classical: mean anomaly at epoch (deg)"),
            "epoch": p("string", "Orbit epoch (IO-8601 or STK UTCG)"),
            "coordinate_system": p(
                "string",
                "Classical/Cartesian coordinate system",
                enum=list(CLASSICAL_COORDINATE_SYSTEM),
                default="J2000",
            ),
            "x_km": p("number", "Cartesian: X position (km)"),
            "y_km": p("number", "Cartesian: Y position (km)"),
            "z_km": p("number", "Cartesian: Z position (km)"),
            "vx_km_s": p("number", "Cartesian: X velocity (km/s)"),
            "vy_km_s": p("number", "Cartesian: Y velocity (km/s)"),
            "vz_km_s": p("number", "Cartesian: Z velocity (km/s)"),
            "tle_line1": p("string", "TLE: line 1"),
            "tle_line2": p("string", "TLE: line 2"),
            "file_path": p("string", "From-file: ephemeris file path"),
            "propagate": p("boolean", "Propagate after assigning the state", default=True),
        },
        ["satellite_name"],
    ),
    category="satellite",
    mutating=True,
    returns="orbit assignment and state",
    tags=["satellite", "orbit", "tle"],
)
def satellite_set_orbit(
    session: Any,
    satellite_name: str,
    mode: str = "classical",
    semi_major_axis_km: float | None = None,
    eccentricity: float | None = None,
    inclination_deg: float | None = None,
    raan_deg: float | None = None,
    arg_of_perigee_deg: float | None = None,
    mean_anomaly_deg: float | None = None,
    epoch: str | None = None,
    coordinate_system: str = "J2000",
    x_km: float | None = None,
    y_km: float | None = None,
    z_km: float | None = None,
    vx_km_s: float | None = None,
    vy_km_s: float | None = None,
    vz_km_s: float | None = None,
    tle_line1: str | None = None,
    tle_line2: str | None = None,
    file_path: str | None = None,
    propagate: bool = True,
) -> dict[str, Any]:
    sat = _satellite(session, satellite_name)
    mode = (mode or "classical").lower()
    coord = _coordinate_code(coordinate_system)
    prop = sat.Propagator

    if mode == "classical":
        required = {
            "semi_major_axis_km": semi_major_axis_km,
            "eccentricity": eccentricity,
            "inclination_deg": inclination_deg,
            "raan_deg": raan_deg,
            "arg_of_perigee_deg": arg_of_perigee_deg,
            "mean_anomaly_deg": mean_anomaly_deg,
        }
        missing = [key for key, value in required.items() if value is None]
        if missing:
            raise StkValidationError(
                "classical mode requires: " + ", ".join(missing)
            )
        if semi_major_axis_km <= 0:
            raise StkValidationError("semi_major_axis_km must be positive")
        if not 0 <= eccentricity < 1:
            raise StkValidationError("eccentricity must be in [0, 1)")
        rep = prop.InitialState.Representation
        if epoch:
            try:
                rep.Epoch = format_stk(parse_time(epoch))
            except Exception as exc:
                raise wrap_com_error(exc, "Setting orbit epoch") from exc
        try:
            rep.AssignClassical(
                coord,
                float(semi_major_axis_km),
                float(eccentricity),
                float(inclination_deg),
                float(arg_of_perigee_deg),
                float(raan_deg),
                float(mean_anomaly_deg),
            )
        except Exception as exc:
            raise wrap_com_error(exc, "AssignClassical") from exc
    elif mode == "cartesian":
        required = {
            "x_km": x_km,
            "y_km": y_km,
            "z_km": z_km,
            "vx_km_s": vx_km_s,
            "vy_km_s": vy_km_s,
            "vz_km_s": vz_km_s,
        }
        missing = [key for key, value in required.items() if value is None]
        if missing:
            raise StkValidationError("cartesian mode requires: " + ", ".join(missing))
        rep = prop.InitialState.Representation
        if epoch:
            try:
                rep.Epoch = format_stk(parse_time(epoch))
            except Exception as exc:
                raise wrap_com_error(exc, "Setting orbit epoch") from exc
        try:
            rep.AssignCartesian(
                coord,
                float(x_km),
                float(y_km),
                float(z_km),
                float(vx_km_s),
                float(vy_km_s),
                float(vz_km_s),
            )
        except Exception as exc:
            raise wrap_com_error(exc, "AssignCartesian") from exc
    elif mode == "tle":
        if not tle_line1 or not tle_line2:
            raise StkValidationError("tle mode requires tle_line1 and tle_line2")
        try:
            sat.SetPropagatorType(propagator_code("SGP4"))
        except Exception as exc:
            raise wrap_com_error(exc, "SetPropagatorType(SGP4)") from exc
        command = (
            f'SetState {_connect_path(sat)} TLE "{tle_line1.strip()}" "{tle_line2.strip()}"'
        )
        # Prefer COM: the Connect port is process-global, so a second running STK
        # version can own 5001 and receive the command for the wrong scenario.
        try:
            result = session.execute_command(command, transport="com")
        except Exception:
            result = session.execute_command(command, transport="tcp")
        if result.get("ack") == "NAK":
            raise StkOperationError("STK rejected the TLE", details=result)
        # COM's ExecuteCommand can return before the propagator has refreshed
        # its state; propagation below makes the new TLE effective.
    elif mode == "from_file":
        if not file_path:
            raise StkValidationError("from_file mode requires file_path")
        path = Path(file_path).expanduser()
        if not path.exists():
            raise StkOperationError(f"Ephemeris file not found: {path}")
        try:
            sat.SetPropagatorType(propagator_code("StkExternal"))
        except Exception:
            pass
        command = f'SetState {_connect_path(sat)} FromFile "{path}"'
        try:
            result = session.execute_command(command, transport="com")
        except Exception:
            result = session.execute_command(command, transport="tcp")
        if result.get("ack") == "NAK":
            raise StkOperationError("STK did not accept the ephemeris file", details=result)
    else:
        raise StkValidationError(f"Unknown orbit mode: {mode!r}")

    if propagate:
        _propagate(sat)
    return {
        "satellite": str(sat.InstanceName),
        "mode": mode,
        "coordinate_system": coordinate_system,
        "epoch": _safe_epoch(sat, epoch),
        "propagated": bool(propagate),
        "state": satellite_state(session, str(sat.InstanceName)),
    }


def _safe_epoch(sat: Any, fallback: str | None) -> str | None:
    try:
        return str(sat.Propagator.InitialState.Representation.Epoch)
    except Exception:
        return fallback


def _connect_path(obj: Any) -> str:
    from ..stk_common import truncated_path

    return truncated_path(obj)


@tool(
    "satellite_propagate",
    "Propagate the satellite ephemeris to the scenario time interval.",
    object_schema(
        {
            "satellite_name": p("string", "Satellite name"),
            "use_scenario_time": p(
                "boolean", "Use the scenario analysis interval", default=True
            ),
        },
        ["satellite_name"],
    ),
    category="satellite",
    mutating=True,
    returns="propagation result",
)
def satellite_propagate(
    session: Any, satellite_name: str, use_scenario_time: bool = True
) -> dict[str, Any]:
    sat = _satellite(session, satellite_name)
    try:
        if use_scenario_time:
            try:
                sat.Propagator.UseScenarioAnalysisTime = True
            except Exception:
                pass
        sat.Propagator.Propagate()
    except Exception as exc:
        raise wrap_com_error(exc, f"Propagating {satellite_name}") from exc
    return {
        "satellite": str(sat.InstanceName),
        "propagated": True,
        "state": satellite_state(session, satellite_name),
    }


@tool(
    "satellite_state",
    "Query a satellite's Cartesian position/velocity, LLA and classical elements "
    "at a specific time or at the scenario start.",
    object_schema(
        {
            "satellite_name": p("string", "Satellite name"),
            "time": p("string", "Query time (defaults to scenario start)"),
            "frame": p(
                "string",
                "Cartesian frame group",
                enum=["ICRF", "J2000", "Fixed", "TrueOfDate", "MeanOfDate"],
                default="ICRF",
            ),
        },
        ["satellite_name"],
    ),
    category="analysis",
    returns="state vectors",
)
def satellite_state(
    session: Any,
    satellite_name: str,
    time: str | None = None,
    frame: str = "ICRF",
) -> dict[str, Any]:
    sat = _satellite(session, satellite_name)
    query_time = format_stk(parse_time(time, default=parse_time(str(session.scenario.StartTime))))
    result: dict[str, Any] = {
        "satellite": str(sat.InstanceName),
        "time": query_time,
        "frame": frame,
    }
    for provider, key in (
        ("Cartesian Position", "position"),
        ("Cartesian Velocity", "velocity"),
    ):
        try:
            table = query_data_provider(
                sat, provider, frame, time=query_time, max_rows=1
            )
            row = table["rows"][0] if table["rows"] else {}
            result[key] = row
        except Exception as exc:
            result[f"{key}_error"] = str(exc)
    # LLA State has its own group set; try Geodetic then the first group.
    try:
        dp = sat.DataProviders.Item("LLA State")
        groups = [str(dp.Group.Item(i).Name) for i in range(dp.Group.Count)]
        group = "Fixed" if "Fixed" in groups else (groups[0] if groups else "Fixed")
        table = query_data_provider(sat, "LLA State", group, time=query_time, max_rows=1)
        result["lla"] = table["rows"][0] if table["rows"] else {}
        result["lla_group"] = group
    except Exception as exc:
        result["lla_error"] = str(exc)
    try:
        table = query_data_provider(
            sat, "Classical Elements", "J2000", time=query_time, max_rows=1
        )
        result["classical"] = table["rows"][0] if table["rows"] else {}
    except Exception as exc:
        result["classical_error"] = str(exc)
    return result


@tool(
    "satellite_tle_summary",
    "Read the TLE summary data provider for a satellite (epoch, elements, validity).",
    object_schema(
        {
            "satellite_name": p("string", "Satellite name"),
            "max_rows": p("integer", "Maximum rows", default=50),
        },
        ["satellite_name"],
    ),
    category="analysis",
    returns="TLE summary",
)
def satellite_tle_summary(session: Any, satellite_name: str, max_rows: int = 50) -> dict[str, Any]:
    sat = _satellite(session, satellite_name)
    return query_data_provider(sat, "TLE Summary Data", max_rows=max_rows)


@tool(
    "satellite_ephemeris",
    "Sample a satellite ephemeris over an interval and optionally write a CSV file.",
    object_schema(
        {
            "satellite_name": p("string", "Satellite name"),
            "start_time": p("string", "Start time (defaults to scenario start)"),
            "stop_time": p("string", "Stop time (defaults to scenario stop)"),
            "step_sec": p("number", "Sampling step in seconds", default=60),
            "frame": p(
                "string",
                "Cartesian frame group",
                enum=["ICRF", "J2000", "Fixed", "TrueOfDate", "MeanOfDate"],
                default="ICRF",
            ),
            "include_lla": p("boolean", "Also include LLA columns", default=True),
            "output_path": p("string", "Optional CSV output path"),
            "max_rows": p("integer", "Maximum returned rows", default=2000),
        },
        ["satellite_name"],
    ),
    category="analysis",
    returns="ephemeris rows",
)
def satellite_ephemeris(
    session: Any,
    satellite_name: str,
    start_time: str | None = None,
    stop_time: str | None = None,
    step_sec: float = 60.0,
    frame: str = "ICRF",
    include_lla: bool = True,
    output_path: str | None = None,
    max_rows: int = 2000,
) -> dict[str, Any]:
    sat = _satellite(session, satellite_name)
    sc = session.scenario
    start, stop = resolve_interval(
        start_time,
        stop_time,
        default_start=parse_time(str(sc.StartTime)),
        duration_hours=(parse_time(str(sc.StopTime)) - parse_time(str(sc.StartTime))).total_seconds() / 3600,
    )
    position = query_data_provider(
        sat,
        "Cartesian Position",
        frame,
        start_time=format_stk(start),
        stop_time=format_stk(stop),
        step_sec=step_sec,
        max_rows=max_rows,
    )
    velocity = query_data_provider(
        sat,
        "Cartesian Velocity",
        frame,
        start_time=format_stk(start),
        stop_time=format_stk(stop),
        step_sec=step_sec,
        max_rows=max_rows,
    )
    rows = []
    for index, row in enumerate(position["rows"]):
        merged = dict(row)
        if index < len(velocity["rows"]):
            for key, value in velocity["rows"][index].items():
                if key != "Time":
                    merged[f"v{key}"] = value
        rows.append(merged)
    if include_lla:
        try:
            dp = sat.DataProviders.Item("LLA State")
            groups = [str(dp.Group.Item(i).Name) for i in range(dp.Group.Count)]
            lla_group = "Fixed" if "Fixed" in groups else (groups[0] if groups else "Fixed")
            lla = query_data_provider(
                sat,
                "LLA State",
                lla_group,
                start_time=format_stk(start),
                stop_time=format_stk(stop),
                step_sec=step_sec,
                max_rows=max_rows,
            )
            for index, row in enumerate(rows):
                if index < len(lla["rows"]):
                    for key, value in lla["rows"][index].items():
                        if key != "Time":
                            merged_key = f"lla_{key}"
                            row[merged_key] = value
        except Exception:
            pass
    result: dict[str, Any] = {
        "satellite": str(sat.InstanceName),
        "start_time": format_stk(start),
        "stop_time": format_stk(stop),
        "step_sec": step_sec,
        "frame": frame,
        "row_count": len(rows),
        "columns": list(rows[0].keys()) if rows else [],
        "rows": rows,
        "truncated": len(rows) >= max_rows,
    }
    if output_path:
        target = Path(output_path).expanduser()
        if not target.is_absolute():
            target = session.settings.data_dir / target
        write_csv(target, result["columns"], rows)
        result["output_path"] = str(target)
        result["output_size"] = target.stat().st_size if target.exists() else 0
    return result


@tool(
    "astrogator_summary",
    "List the Astrogator main-sequence segments for a satellite.",
    object_schema({"satellite_name": p("string", "Satellite name")}, ["satellite_name"]),
    category="astrogator",
    returns="segment list",
)
def astrogator_summary(session: Any, satellite_name: str) -> dict[str, Any]:
    sat = _satellite(session, satellite_name)
    prop = sat.Propagator
    try:
        if int(getattr(sat, "PropagatorType", -1)) != 12:
            raise StkValidationError(
                f"{satellite_name} is not using the Astrogator propagator",
                hint="Call satellite_set_propagator with 'Astrogator' first.",
            )
        sequence = prop.MainSequence
        segments = []
        for index in range(int(sequence.Count)):
            segment = sequence.Item(index)
            segments.append(
                {
                    "index": index,
                    "name": str(segment.Name),
                    "type": int(getattr(segment, "Type", -1)),
                    "description": str(getattr(segment, "Description", "")),
                    "exec_summary": str(getattr(segment, "ExecSummary", "")),
                }
            )
    except StkValidationError:
        raise
    except Exception as exc:
        raise wrap_com_error(exc, f"Reading Astrogator sequence for {satellite_name}") from exc
    return {"satellite": str(sat.InstanceName), "segment_count": len(segments), "segments": segments}


@tool(
    "astrogator_run",
    "Run the Astrogator main sequence (RunMCS) and return the resulting state.",
    object_schema({"satellite_name": p("string", "Satellite name")}, ["satellite_name"]),
    category="astrogator",
    mutating=True,
    returns="run result and state",
)
def astrogator_run(session: Any, satellite_name: str) -> dict[str, Any]:
    sat = _satellite(session, satellite_name)
    try:
        if int(getattr(sat, "PropagatorType", -1)) != 12:
            raise StkValidationError(
                f"{satellite_name} is not using the Astrogator propagator",
                hint="Call satellite_set_propagator with 'Astrogator' first.",
            )
        prop = sat.Propagator
        prop.RunMCS()
    except StkValidationError:
        raise
    except Exception as exc:
        raise wrap_com_error(exc, f"Running Astrogator for {satellite_name}") from exc
    return {
        "satellite": str(sat.InstanceName),
        "run": True,
        "state": satellite_state(session, satellite_name),
    }


@tool(
    "satellite_set_propagator",
    "Change the propagator of an existing satellite (TwoBody, J2, J4, HPOP, SGP4).",
    object_schema(
        {
            "satellite_name": p("string", "Satellite name"),
            "propagator": p(
                "string",
                "New propagator",
                enum=["TwoBody", "J2Perturbation", "J4Perturbation", "HPOP", "SGP4"],
            ),
        },
        ["satellite_name", "propagator"],
    ),
    category="satellite",
    mutating=True,
    returns="propagator change",
)
def satellite_set_propagator(
    session: Any, satellite_name: str, propagator: str
) -> dict[str, Any]:
    sat = _satellite(session, satellite_name)
    prop_name = normalize_propagator(propagator)
    try:
        sat.SetPropagatorType(propagator_code(prop_name))
    except Exception as exc:
        raise wrap_com_error(exc, "SetPropagatorType") from exc
    return {
        "satellite": str(sat.InstanceName),
        "propagator": prop_name,
        "propagator_code": propagator_code(prop_name),
    }


@tool(
    "satellite_list",
    "List satellites in the current scenario.",
    object_schema({}),
    category="satellite",
    returns="satellite list",
)
def satellite_list(session: Any) -> list[dict[str, Any]]:
    sc = session.scenario
    satellites = []
    for index in range(int(sc.Children.Count)):
        obj = sc.Children.Item(index)
        if str(obj.ClassName) == "Satellite":
            satellites.append(object_summary(obj))
    return satellites
