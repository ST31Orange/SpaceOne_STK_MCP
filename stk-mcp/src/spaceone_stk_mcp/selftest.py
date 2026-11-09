"""End-to-end STK smoke test used by the CLI, REST API and ``stk_selftest``."""

from __future__ import annotations

import logging
import shutil
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from .errors import StkMcpError
from .serialization import jsonable
from .stk_common import (
    assign_geodetic,
    compute_access,
    new_object,
    query_data_provider,
    report_create,
)
from .timeutil import format_stk

logger = logging.getLogger(__name__)


def _safe(value: Any) -> Any:
    try:
        return jsonable(value)
    except Exception:
        return str(value)


def _step(steps: list[dict[str, Any]], name: str, fn: Callable[[], Any]) -> Any:
    started = time.perf_counter()
    try:
        value = fn()
        steps.append(
            {
                "step": name,
                "ok": True,
                "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                "result": _safe(value),
            }
        )
        return value
    except Exception as exc:
        steps.append(
            {
                "step": name,
                "ok": False,
                "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                "error": str(exc),
            }
        )
        logger.warning("Self-test step %s failed: %s", name, exc)
        return None


def run_selftest(session: Any, *, replace_scenario: bool = False) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []
    started = time.perf_counter()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    scenario_name = f"MCP_SelfTest_{timestamp}"
    work_dir = session.settings.data_dir / "selftest" / timestamp
    scenario_path = work_dir / f"{scenario_name}.sc"
    report_path = work_dir / "access_report.txt"
    created_scenario = False

    def _status() -> dict[str, Any]:
        return {
            "connected": session.connected,
            "version": session.version,
            "prog_id": session.prog_id,
        }

    _step(steps, "session_status", _status)

    current = None
    try:
        current = session.root.CurrentScenario
    except Exception:
        current = None

    if current is not None and not replace_scenario:
        # Non-destructive mode: exercise read-only paths on the user's scenario.
        _step(steps, "scenario_info", lambda: {
            "name": str(current.InstanceName),
            "start": str(current.StartTime),
            "stop": str(current.StopTime),
            "children": int(current.Children.Count),
        })
        first_satellite = None
        for i in range(int(current.Children.Count)):
            child = current.Children.Item(i)
            if str(child.ClassName) == "Satellite":
                first_satellite = child
                break
        if first_satellite is not None:
            _step(steps, "satellite_state_readonly", lambda: query_data_provider(
                first_satellite, "Cartesian Position", "ICRF",
                time=str(current.StartTime), max_rows=1,
            ))
            _step(steps, "data_provider_list_readonly", lambda: {
                "count": int(first_satellite.DataProviders.Count)
            })
        else:
            steps.append({"step": "satellite_readonly", "ok": True, "skipped": "no satellite in scenario"})
        passed = all(step.get("ok", True) for step in steps)
        return {
            "mode": "read_only",
            "passed": passed,
            "scenario": str(current.InstanceName),
            "steps": steps,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
        }

    try:
        if current is not None and replace_scenario:
            _step(steps, "close_existing_scenario", lambda: session.root.CloseScenario())

        work_dir.mkdir(parents=True, exist_ok=True)

        def _create_scenario() -> dict[str, Any]:
            nonlocal created_scenario
            session.root.NewScenario(scenario_name)
            created_scenario = True
            sc = session.root.CurrentScenario
            now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
            sc.SetTimePeriod(
                format_stk(now), format_stk(now + timedelta(hours=2))
            )
            return {"name": str(sc.InstanceName), "start": str(sc.StartTime), "stop": str(sc.StopTime)}

        _step(steps, "create_scenario", _create_scenario)
        sc = session.root.CurrentScenario
        if sc is None:
            raise StkMcpError("STK did not create the self-test scenario")

        satellite = _step(
            steps,
            "create_satellite",
            lambda: new_object(sc, "Satellite", "SelfTestSat"),
        )
        if satellite is None:
            raise StkMcpError("Could not create the self-test satellite")

        def _orbit() -> dict[str, Any]:
            satellite.SetPropagatorType(7)  # TwoBody
            rep = satellite.Propagator.InitialState.Representation
            rep.AssignClassical(3, 7000.0, 0.001, 97.4, 0.0, 10.0, 0.0)
            satellite.Propagator.Propagate()
            return {"semi_major_axis_km": 7000.0, "inclination_deg": 97.4}

        _step(steps, "set_orbit_and_propagate", _orbit)
        _step(
            steps,
            "query_state",
            lambda: query_data_provider(
                satellite, "Cartesian Position", "ICRF",
                time=str(sc.StartTime), max_rows=1,
            ),
        )

        facility = _step(
            steps,
            "create_facility",
            lambda: _facility(sc),
        )

        if facility is not None:
            _step(
                steps,
                "compute_access",
                lambda: compute_access(satellite, facility),
            )
            _step(
                steps,
                "access_report",
                lambda: report_create(
                    session,
                    satellite,
                    style="Access",
                    file_path=str(report_path),
                    access_object="*/Facility/SelfTestFac",
                ),
            )

        coverage = _step(
            steps,
            "create_coverage",
            lambda: _coverage(sc, satellite),
        )
        if coverage is not None:
            _step(
                steps,
                "coverage_stats",
                lambda: query_data_provider(coverage, "Percent Coverage", max_rows=20),
            )

        _step(
            steps,
            "save_scenario",
            lambda: _save(session, scenario_path),
        )
    except Exception as exc:
        steps.append({"step": "selftest", "ok": False, "error": str(exc)})
    finally:
        if created_scenario:
            try:
                session.root.CloseScenario()
                steps.append({"step": "cleanup_close_scenario", "ok": True})
            except Exception as exc:
                steps.append({"step": "cleanup_close_scenario", "ok": False, "error": str(exc)})
        # The scenario was saved into work_dir; remove generated artifacts after
        # reporting their size.
        try:
            shutil.rmtree(work_dir, ignore_errors=True)
        except Exception:
            pass

    passed = all(step.get("ok", True) for step in steps)
    return {
        "mode": "full",
        "passed": passed,
        "steps": steps,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
        "note": "The self-test created and closed its own scenario; user data was not modified."
        if replace_scenario
        else "No scenario was open, so a temporary scenario was created and closed.",
    }


def _facility(sc: Any) -> Any:
    fac = new_object(sc, "Facility", "SelfTestFac")
    assign_geodetic(fac, 40.0, 116.0, 0.0)
    return fac


def _coverage(sc: Any, satellite: Any) -> Any:
    cov = new_object(sc, "CoverageDefinition", "SelfTestCov")
    cov.Grid.BoundsType = 1  # eBoundsGlobal
    cov.Grid.ResolutionType = 2
    cov.Grid.Resolution.LatLon = 10.0
    cov.AssetList.Add(f"Satellite/{satellite.InstanceName}")
    cov.ComputeAccesses()
    return cov


def _save(session: Any, path: Path) -> dict[str, Any]:
    session.root.SaveScenarioAs(str(path))
    return {"path": str(path), "exists": path.exists(), "size": path.stat().st_size if path.exists() else 0}
