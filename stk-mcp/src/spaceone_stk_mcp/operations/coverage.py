"""Coverage definitions, grids, assets, figures of merit and statistics."""

from __future__ import annotations

from typing import Any

from ..errors import StkOperationError, StkValidationError, wrap_com_error
from ..stk_common import (
    find_object,
    new_object,
    object_summary,
    query_data_provider,
    truncated_path,
)
from ..tooling import object_schema, p, tool


@tool(
    "coverage_create",
    "Create a coverage definition.",
    object_schema(
        {
            "name": p("string", "Coverage definition name"),
            "replace_existing": p("boolean", "Unload an existing coverage definition", default=False),
        },
        ["name"],
    ),
    category="coverage",
    mutating=True,
    returns="coverage info",
)
def coverage_create(session: Any, name: str, replace_existing: bool = False) -> dict[str, Any]:
    cov = new_object(session.scenario, "CoverageDefinition", name, replace=replace_existing)
    return object_summary(cov)


@tool(
    "coverage_set_grid",
    "Set a global or latitude/longitude coverage grid.",
    object_schema(
        {
            "coverage_name": p("string", "Coverage definition name"),
            "mode": p(
                "string",
                "Grid bounds",
                enum=["global", "lat_lon_region", "lat_band"],
                default="global",
            ),
            "min_lat": p("number", "Region minimum latitude", minimum=-90, maximum=90),
            "max_lat": p("number", "Region maximum latitude", minimum=-90, maximum=90),
            "min_lon": p("number", "Region minimum longitude", minimum=-180, maximum=180),
            "max_lon": p("number", "Region maximum longitude", minimum=-180, maximum=180),
            "lat_resolution_deg": p("number", "Latitude resolution (deg)", default=5.0),
            "lon_resolution_deg": p("number", "Longitude resolution (deg)", default=5.0),
        },
        ["coverage_name"],
    ),
    category="coverage",
    mutating=True,
    returns="grid configuration",
)
def coverage_set_grid(
    session: Any,
    coverage_name: str,
    mode: str = "global",
    min_lat: float | None = None,
    max_lat: float | None = None,
    min_lon: float | None = None,
    max_lon: float | None = None,
    lat_resolution_deg: float = 5.0,
    lon_resolution_deg: float = 5.0,
) -> dict[str, Any]:
    cov = _coverage(session, coverage_name)
    mode = (mode or "global").lower()
    try:
        if mode == "global":
            cov.Grid.BoundsType = 1
            cov.Grid.ResolutionType = 2
            cov.Grid.Resolution.LatLon = float(lat_resolution_deg)
        elif mode == "lat_lon_region":
            if None in (min_lat, max_lat, min_lon, max_lon):
                raise StkValidationError(
                    "lat_lon_region requires min_lat, max_lat, min_lon and max_lon"
                )
            # AgECvBounds: eBoundsLatLonRegion = 6. (0 is Custom Regions and 3
            # is a single latitude line, not a lat/lon box.)
            cov.Grid.BoundsType = 6
            bounds = cov.Grid.Bounds
            for attr, value in (
                ("MinLatitude", min_lat),
                ("MaxLatitude", max_lat),
                ("MinLongitude", min_lon),
                ("MaxLongitude", max_lon),
            ):
                try:
                    setattr(bounds, attr, float(value))
                except Exception as exc:
                    raise StkOperationError(
                        f"STK does not expose coverage bound {attr}: {exc}"
                    ) from exc
            cov.Grid.ResolutionType = 2
            try:
                cov.Grid.Resolution.LatLon = (
                    f"{float(lat_resolution_deg)} {float(lon_resolution_deg)}"
                )
            except Exception:
                cov.Grid.Resolution.LatLon = float(lat_resolution_deg)
        elif mode == "lat_band":
            cov.Grid.BoundsType = 2
            bounds = cov.Grid.Bounds
            bounds.MinLatitude = float(min_lat)
            bounds.MaxLatitude = float(max_lat)
            cov.Grid.ResolutionType = 2
            cov.Grid.Resolution.LatLon = float(lat_resolution_deg)
        else:
            raise StkValidationError(f"Unknown grid mode: {mode!r}")
    except StkValidationError:
        raise
    except Exception as exc:
        raise wrap_com_error(exc, "Configuring coverage grid") from exc
    return {
        "coverage": str(cov.InstanceName),
        "mode": mode,
        "min_lat": min_lat,
        "max_lat": max_lat,
        "min_lon": min_lon,
        "max_lon": max_lon,
        "lat_resolution_deg": lat_resolution_deg,
        "lon_resolution_deg": lon_resolution_deg,
    }


def _coverage(session: Any, name: str) -> Any:
    obj = find_object(session, name)
    if str(obj.ClassName) != "CoverageDefinition":
        raise StkValidationError(f"{name} is not a CoverageDefinition")
    return obj


@tool(
    "coverage_add_asset",
    "Assign an object as a coverage asset.",
    object_schema(
        {
            "coverage_name": p("string", "Coverage definition name"),
            "object_name": p("string", "Asset object name"),
        },
        ["coverage_name", "object_name"],
    ),
    category="coverage",
    mutating=True,
    returns="asset assignment",
)
def coverage_add_asset(session: Any, coverage_name: str, object_name: str) -> dict[str, Any]:
    cov = _coverage(session, coverage_name)
    obj = find_object(session, object_name)
    candidates = [
        f"{obj.ClassName}/{obj.InstanceName}",
        truncated_path(obj),
        str(obj.Path),
    ]
    last_error = None
    for candidate in candidates:
        try:
            cov.AssetList.Add(candidate)
            return {
                "coverage": str(cov.InstanceName),
                "asset": str(obj.InstanceName),
                "asset_count": int(cov.AssetList.Count),
                "path_used": candidate,
            }
        except Exception as exc:
            last_error = exc
    raise wrap_com_error(last_error or RuntimeError("AssetList.Add failed"), "Adding coverage asset")


@tool(
    "coverage_remove_asset",
    "Remove an asset from a coverage definition.",
    object_schema(
        {
            "coverage_name": p("string", "Coverage definition name"),
            "object_name": p("string", "Asset object name"),
        },
        ["coverage_name", "object_name"],
    ),
    category="coverage",
    mutating=True,
    returns="asset removal",
)
def coverage_remove_asset(session: Any, coverage_name: str, object_name: str) -> dict[str, Any]:
    cov = _coverage(session, coverage_name)
    obj = find_object(session, object_name)
    for candidate in (f"{obj.ClassName}/{obj.InstanceName}", truncated_path(obj)):
        try:
            cov.AssetList.Remove(candidate)
            return {"coverage": str(cov.InstanceName), "removed": str(obj.InstanceName)}
        except Exception:
            continue
    raise StkOperationError(f"Could not remove {object_name} from coverage {coverage_name}")


@tool(
    "coverage_compute",
    "Compute coverage accesses and return high-level coverage statistics.",
    object_schema({"coverage_name": p("string", "Coverage definition name")}, ["coverage_name"]),
    category="coverage",
    mutating=True,
    returns="coverage statistics",
)
def coverage_compute(session: Any, coverage_name: str) -> dict[str, Any]:
    cov = _coverage(session, coverage_name)
    try:
        cov.ComputeAccesses()
    except Exception as exc:
        raise wrap_com_error(exc, "ComputeAccesses") from exc
    return {
        "coverage": str(cov.InstanceName),
        "computed": True,
        "asset_count": int(cov.AssetList.Count),
        "statistics": _coverage_stats(cov),
    }


def _coverage_stats(cov: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for provider in ("Percent Coverage", "Coverage Definition", "Global Coverage"):
        try:
            table = query_data_provider(cov, provider, max_rows=6)
            rows = table["rows"]
            if not rows:
                continue
            if provider == "Coverage Definition":
                result[provider] = rows
            elif len(rows) == 1:
                result[provider] = rows[0]
            else:
                result[provider] = {
                    "first": rows[0],
                    "last": rows[-1],
                    "row_count": table["row_count"],
                    "truncated": table["truncated"],
                }
        except Exception as exc:
            result[f"{provider}_error"] = str(exc)
    return result


@tool(
    "coverage_stats",
    "Read coverage statistics without recomputing accesses.",
    object_schema(
        {
            "coverage_name": p("string", "Coverage definition name"),
            "provider": p(
                "string",
                "Coverage data provider",
                default="Percent Coverage",
            ),
            "max_rows": p("integer", "Maximum rows", default=200),
        },
        ["coverage_name"],
    ),
    category="coverage",
    returns="coverage data",
)
def coverage_stats(
    session: Any, coverage_name: str, provider: str = "Percent Coverage", max_rows: int = 200
) -> dict[str, Any]:
    cov = _coverage(session, coverage_name)
    return query_data_provider(cov, provider, max_rows=max_rows)


@tool(
    "coverage_fom_create",
    "Create a Figure of Merit under a coverage definition and optionally set its type.",
    object_schema(
        {
            "coverage_name": p("string", "Coverage definition name"),
            "name": p("string", "Figure-of-merit name", default="FOM1"),
            "definition_type": p(
                "integer",
                "STK FOM definition type index (0 = default Coverage)",
                default=0,
            ),
        },
        ["coverage_name"],
    ),
    category="coverage",
    mutating=True,
    returns="FOM info",
)
def coverage_fom_create(
    session: Any, coverage_name: str, name: str = "FOM1", definition_type: int = 0
) -> dict[str, Any]:
    cov = _coverage(session, coverage_name)
    try:
        fom = cov.Children.New(25, name)
        if definition_type:
            fom.SetDefinitionType(int(definition_type))
        supported = []
        try:
            supported = [str(item) for item in fom.DefinitionSupportedTypes]
        except Exception:
            pass
        return {
            **object_summary(fom),
            "coverage": str(cov.InstanceName),
            "definition_type": int(getattr(fom, "DefinitionType", definition_type)),
            "supported_types": supported,
        }
    except Exception as exc:
        raise wrap_com_error(exc, f"Creating FOM {name}") from exc


@tool(
    "coverage_fom_query",
    "Query a figure-of-merit data provider.",
    object_schema(
        {
            "coverage_name": p("string", "Coverage definition name"),
            "fom_name": p("string", "FOM name"),
            "provider": p("string", "FOM data provider", default="FOM Value"),
            "max_rows": p("integer", "Maximum rows", default=200),
        },
        ["coverage_name", "fom_name"],
    ),
    category="coverage",
    returns="FOM data",
)
def coverage_fom_query(
    session: Any, coverage_name: str, fom_name: str, provider: str = "FOM Value", max_rows: int = 200
) -> dict[str, Any]:
    cov = _coverage(session, coverage_name)
    try:
        fom = cov.Children.Item(fom_name)
    except Exception:
        fom = find_object(session, fom_name)
    return query_data_provider(fom, provider, max_rows=max_rows)


@tool(
    "coverage_grid_inspector",
    "Select a grid point and read its point/region coverage values.",
    object_schema(
        {
            "coverage_name": p("string", "Coverage definition name"),
            "latitude_deg": p("number", "Grid point latitude", minimum=-90, maximum=90),
            "longitude_deg": p("number", "Grid point longitude", minimum=-180, maximum=180),
        },
        ["coverage_name", "latitude_deg", "longitude_deg"],
    ),
    category="coverage",
    mutating=True,
    returns="point coverage",
)
def coverage_grid_inspector(
    session: Any, coverage_name: str, latitude_deg: float, longitude_deg: float
) -> dict[str, Any]:
    cov = _coverage(session, coverage_name)
    try:
        inspector = cov.GridInspector
        inspector.SelectPoint(latitude_deg, longitude_deg)
        payload: dict[str, Any] = {
            "coverage": str(cov.InstanceName),
            "latitude_deg": latitude_deg,
            "longitude_deg": longitude_deg,
        }
        for attr in ("PointCoverage", "PointDailyCoverage", "PointProbOfCoverage"):
            try:
                payload[attr] = str(getattr(inspector, attr))
            except Exception:
                continue
        return payload
    except Exception as exc:
        raise wrap_com_error(exc, "GridInspector") from exc
