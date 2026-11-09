"""Ground objects, sensors, constellations, chains, platforms and object CRUD."""

from __future__ import annotations

from typing import Any

from ..enums import OBJECT_TYPE, SENSOR_PATTERN, propagator_code, sensor_pattern_code
from ..errors import StkOperationError, StkValidationError, wrap_com_error
from ..stk_common import (
    assign_geodetic,
    child_list,
    find_object,
    new_object,
    object_summary,
    truncated_path,
    validate_name,
)
from ..tooling import object_schema, p, tool


def _object_listing(obj: Any, max_depth: int, depth: int = 0) -> list[dict[str, Any]]:
    rows = [object_summary(obj)]
    if depth >= max_depth:
        return rows
    for child in child_list(obj):
        rows.extend(_object_listing(child, max_depth, depth + 1))
    return rows


@tool(
    "object_list",
    "List objects in the scenario, optionally filtered by class and including "
    "nested children such as sensors and equipment.",
    object_schema(
        {
            "class_name": p(
                "string",
                "Filter by ClassName, e.g. Satellite, Facility, Sensor, CoverageDefinition",
            ),
            "include_children": p("boolean", "Recurse into child objects", default=True),
            "max_depth": p("integer", "Maximum recursion depth", default=3, minimum=0, maximum=8),
        }
    ),
    category="objects",
    returns="object list",
)
def object_list(
    session: Any,
    class_name: str | None = None,
    include_children: bool = True,
    max_depth: int = 3,
) -> dict[str, Any]:
    sc = session.scenario
    rows: list[dict[str, Any]] = []
    for child in child_list(sc):
        if include_children:
            rows.extend(_object_listing(child, max_depth, 0))
        else:
            rows.append(object_summary(child))
    if class_name:
        wanted = class_name.lower()
        rows = [row for row in rows if str(row.get("class_name", "")).lower() == wanted]
    return {"scenario": str(sc.InstanceName), "count": len(rows), "objects": rows}


@tool(
    "object_info",
    "Return detailed metadata for one object and optionally its children.",
    object_schema(
        {
            "object_name": p("string", "Object name or path"),
            "include_children": p("boolean", "Include direct children", default=True),
        },
        ["object_name"],
    ),
    category="objects",
    returns="object info",
)
def object_info(session: Any, object_name: str, include_children: bool = True) -> dict[str, Any]:
    obj = find_object(session, object_name)
    return object_summary(obj, children=include_children)


@tool(
    "object_delete",
    "Unload an object from the scenario.",
    object_schema({"object_name": p("string", "Object name or path")}, ["object_name"]),
    category="objects",
    mutating=True,
    returns="delete result",
)
def object_delete(session: Any, object_name: str) -> dict[str, Any]:
    obj = find_object(session, object_name)
    name = str(obj.InstanceName)
    try:
        obj.Unload()
    except Exception as exc:
        raise wrap_com_error(exc, f"Unloading {name}") from exc
    path = ""
    try:
        path = str(obj.Path)
    except Exception:
        pass
    return {"deleted": name, "path": path}


@tool(
    "facility_create",
    "Create a ground facility at a geodetic position.",
    object_schema(
        {
            "name": p("string", "Facility name"),
            "latitude_deg": p("number", "Latitude (-90..90)", minimum=-90, maximum=90),
            "longitude_deg": p("number", "Longitude (-180..180)", minimum=-180, maximum=180),
            "altitude_km": p("number", "Altitude above the ellipsoid (km)", default=0.0),
            "replace_existing": p("boolean", "Unload an existing facility with this name", default=False),
        },
        ["name", "latitude_deg", "longitude_deg"],
    ),
    category="objects",
    mutating=True,
    returns="facility info",
)
def facility_create(
    session: Any,
    name: str,
    latitude_deg: float,
    longitude_deg: float,
    altitude_km: float = 0.0,
    replace_existing: bool = False,
) -> dict[str, Any]:
    sc = session.scenario
    facility = new_object(sc, "Facility", name, replace=replace_existing)
    assign_geodetic(facility, latitude_deg, longitude_deg, altitude_km)
    return {
        **object_summary(facility),
        "latitude_deg": latitude_deg,
        "longitude_deg": longitude_deg,
        "altitude_km": altitude_km,
    }


@tool(
    "facility_set_position",
    "Move an existing facility.",
    object_schema(
        {
            "facility_name": p("string", "Facility name"),
            "latitude_deg": p("number", "Latitude (-90..90)", minimum=-90, maximum=90),
            "longitude_deg": p("number", "Longitude (-180..180)", minimum=-180, maximum=180),
            "altitude_km": p("number", "Altitude (km)", default=0.0),
        },
        ["facility_name", "latitude_deg", "longitude_deg"],
    ),
    category="objects",
    mutating=True,
    returns="facility info",
)
def facility_set_position(
    session: Any,
    facility_name: str,
    latitude_deg: float,
    longitude_deg: float,
    altitude_km: float = 0.0,
) -> dict[str, Any]:
    obj = find_object(session, facility_name)
    if str(obj.ClassName) != "Facility":
        raise StkValidationError(f"{facility_name} is not a Facility")
    assign_geodetic(obj, latitude_deg, longitude_deg, altitude_km)
    return {
        **object_summary(obj),
        "latitude_deg": latitude_deg,
        "longitude_deg": longitude_deg,
        "altitude_km": altitude_km,
    }


@tool(
    "place_create",
    "Create a point place at a geodetic position.",
    object_schema(
        {
            "name": p("string", "Place name"),
            "latitude_deg": p("number", "Latitude (-90..90)", minimum=-90, maximum=90),
            "longitude_deg": p("number", "Longitude (-180..180)", minimum=-180, maximum=180),
            "altitude_km": p("number", "Altitude (km)", default=0.0),
            "replace_existing": p("boolean", "Unload an existing place with this name", default=False),
        },
        ["name", "latitude_deg", "longitude_deg"],
    ),
    category="objects",
    mutating=True,
    returns="place info",
)
def place_create(
    session: Any,
    name: str,
    latitude_deg: float,
    longitude_deg: float,
    altitude_km: float = 0.0,
    replace_existing: bool = False,
) -> dict[str, Any]:
    place = new_object(session.scenario, "Place", name, replace=replace_existing)
    assign_geodetic(place, latitude_deg, longitude_deg, altitude_km)
    return {
        **object_summary(place),
        "latitude_deg": latitude_deg,
        "longitude_deg": longitude_deg,
        "altitude_km": altitude_km,
    }


@tool(
    "place_set_position",
    "Move an existing point place.",
    object_schema(
        {
            "place_name": p("string", "Place name"),
            "latitude_deg": p("number", "Latitude (-90..90)", minimum=-90, maximum=90),
            "longitude_deg": p("number", "Longitude (-180..180)", minimum=-180, maximum=180),
            "altitude_km": p("number", "Altitude (km)", default=0.0),
        },
        ["place_name", "latitude_deg", "longitude_deg"],
    ),
    category="objects",
    mutating=True,
    returns="place info",
)
def place_set_position(
    session: Any,
    place_name: str,
    latitude_deg: float,
    longitude_deg: float,
    altitude_km: float = 0.0,
) -> dict[str, Any]:
    obj = find_object(session, place_name)
    if str(obj.ClassName) != "Place":
        raise StkValidationError(f"{place_name} is not a Place")
    assign_geodetic(obj, latitude_deg, longitude_deg, altitude_km)
    return {
        **object_summary(obj),
        "latitude_deg": latitude_deg,
        "longitude_deg": longitude_deg,
        "altitude_km": altitude_km,
    }


@tool(
    "area_target_create",
    "Create a ground area target, optionally as an ellipse.",
    object_schema(
        {
            "name": p("string", "Area target name"),
            "center_lat": p("number", "Ellipse center latitude", minimum=-90, maximum=90),
            "center_lon": p("number", "Ellipse center longitude", minimum=-180, maximum=180),
            "semi_major_axis_km": p("number", "Ellipse semi-major axis (km)"),
            "semi_minor_axis_km": p("number", "Ellipse semi-minor axis (km)"),
            "bearing_deg": p("number", "Ellipse bearing (deg)", default=0.0),
            "replace_existing": p("boolean", "Unload an existing area target", default=False),
        },
        ["name"],
    ),
    category="objects",
    mutating=True,
    returns="area target info",
)
def area_target_create(
    session: Any,
    name: str,
    center_lat: float | None = None,
    center_lon: float | None = None,
    semi_major_axis_km: float | None = None,
    semi_minor_axis_km: float | None = None,
    bearing_deg: float = 0.0,
    replace_existing: bool = False,
) -> dict[str, Any]:
    area = new_object(session.scenario, "AreaTarget", name, replace=replace_existing)
    result = object_summary(area)
    if None not in (center_lat, center_lon, semi_major_axis_km, semi_minor_axis_km):
        result.update(
            _set_area_ellipse(
                area,
                center_lat,
                center_lon,
                semi_major_axis_km,
                semi_minor_axis_km,
                bearing_deg,
            )
        )
    return result


def _set_area_ellipse(
    area: Any,
    center_lat: float,
    center_lon: float,
    semi_major_axis_km: float,
    semi_minor_axis_km: float,
    bearing_deg: float,
) -> dict[str, Any]:
    try:
        area.AreaType = 0  # eEllipse
        area.Position.AssignGeodetic(center_lat, center_lon, 0.0)
        data = area.AreaTypeData
        data.SemiMajorAxis = float(semi_major_axis_km)
        data.SemiMinorAxis = float(semi_minor_axis_km)
        data.Bearing = float(bearing_deg)
    except Exception as exc:
        raise wrap_com_error(exc, f"Configuring ellipse on {area.InstanceName}") from exc
    return {
        "area_type": "ellipse",
        "center_lat": center_lat,
        "center_lon": center_lon,
        "semi_major_axis_km": semi_major_axis_km,
        "semi_minor_axis_km": semi_minor_axis_km,
        "bearing_deg": bearing_deg,
    }


@tool(
    "area_target_set_ellipse",
    "Configure an existing area target as an ellipse.",
    object_schema(
        {
            "area_target_name": p("string", "Area target name"),
            "center_lat": p("number", "Center latitude", minimum=-90, maximum=90),
            "center_lon": p("number", "Center longitude", minimum=-180, maximum=180),
            "semi_major_axis_km": p("number", "Semi-major axis (km)"),
            "semi_minor_axis_km": p("number", "Semi-minor axis (km)"),
            "bearing_deg": p("number", "Bearing (deg)", default=0.0),
        },
        ["area_target_name", "center_lat", "center_lon", "semi_major_axis_km", "semi_minor_axis_km"],
    ),
    category="objects",
    mutating=True,
    returns="area target info",
)
def area_target_set_ellipse(
    session: Any,
    area_target_name: str,
    center_lat: float,
    center_lon: float,
    semi_major_axis_km: float,
    semi_minor_axis_km: float,
    bearing_deg: float = 0.0,
) -> dict[str, Any]:
    area = find_object(session, area_target_name)
    if str(area.ClassName) != "AreaTarget":
        raise StkValidationError(f"{area_target_name} is not an AreaTarget")
    return {
        **object_summary(area),
        **_set_area_ellipse(
            area, center_lat, center_lon, semi_major_axis_km, semi_minor_axis_km, bearing_deg
        ),
    }


@tool(
    "area_target_set_polygon",
    "Configure an existing area target as a polygon boundary from lat/lon points.",
    object_schema(
        {
            "area_target_name": p("string", "Area target name"),
            "points": p(
                "array",
                "Boundary points in order",
                items={
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "latitude_deg": {"type": "number", "description": "Latitude (-90..90)"},
                        "longitude_deg": {"type": "number", "description": "Longitude (-180..180)"},
                    },
                    "required": ["latitude_deg", "longitude_deg"],
                },
            ),
            "clear_existing": p("boolean", "Remove existing boundary points first", default=True),
        },
        ["area_target_name", "points"],
    ),
    category="objects",
    mutating=True,
    returns="area target polygon info",
)
def area_target_set_polygon(
    session: Any,
    area_target_name: str,
    points: list[dict[str, float]],
    clear_existing: bool = True,
) -> dict[str, Any]:
    area = find_object(session, area_target_name)
    if str(area.ClassName) != "AreaTarget":
        raise StkValidationError(f"{area_target_name} is not an AreaTarget")
    if len(points) < 3:
        raise StkValidationError("polygon requires at least 3 boundary points")
    try:
        area.AreaType = 1  # AgEAreaType ePattern
        data = area.AreaTypeData
        if clear_existing:
            data.RemoveAll()
        for point in points:
            lat = float(point["latitude_deg"])
            lon = float(point["longitude_deg"])
            if not -90 <= lat <= 90 or not -180 <= lon <= 180:
                raise StkValidationError(f"invalid polygon point: {point}")
            data.Add(lat, lon)
    except StkValidationError:
        raise
    except Exception as exc:
        raise wrap_com_error(exc, f"Configuring polygon on {area_target_name}") from exc
    return {
        **object_summary(area),
        "area_type": "polygon",
        "point_count": int(data.Count),
        "points": points,
    }


@tool(
    "area_target_add_boundary_point",
    "Append one boundary point to an area target (switches it to polygon mode).",
    object_schema(
        {
            "area_target_name": p("string", "Area target name"),
            "latitude_deg": p("number", "Latitude (-90..90)", minimum=-90, maximum=90),
            "longitude_deg": p("number", "Longitude (-180..180)", minimum=-180, maximum=180),
        },
        ["area_target_name", "latitude_deg", "longitude_deg"],
    ),
    category="objects",
    mutating=True,
    returns="area target info",
)
def area_target_add_boundary_point(
    session: Any, area_target_name: str, latitude_deg: float, longitude_deg: float
) -> dict[str, Any]:
    area = find_object(session, area_target_name)
    if str(area.ClassName) != "AreaTarget":
        raise StkValidationError(f"{area_target_name} is not an AreaTarget")
    try:
        if int(area.AreaType) != 1:
            area.AreaType = 1
        data = area.AreaTypeData
        data.Add(float(latitude_deg), float(longitude_deg))
    except Exception as exc:
        raise wrap_com_error(exc, f"Adding boundary point to {area_target_name}") from exc
    return {
        "area_target": str(area.InstanceName),
        "point_count": int(data.Count),
        "added": {"latitude_deg": latitude_deg, "longitude_deg": longitude_deg},
    }


@tool(
    "target_set_position",
    "Set a target position from geodetic coordinates or spherical (declination, "
    "right ascension, altitude).",
    object_schema(
        {
            "target_name": p("string", "Target name"),
            "mode": p(
                "string", "Position representation", enum=["geodetic", "spherical"], default="geodetic"
            ),
            "latitude_deg": p("number", "Geodetic latitude (-90..90)", minimum=-90, maximum=90),
            "longitude_deg": p("number", "Geodetic longitude (-180..180)", minimum=-180, maximum=180),
            "altitude_km": p("number", "Altitude (km)", default=0.0),
            "declination_deg": p("number", "Spherical declination (-90..90)", minimum=-90, maximum=90),
            "right_ascension_deg": p("number", "Spherical right ascension (deg)"),
        },
        ["target_name"],
    ),
    category="objects",
    mutating=True,
    returns="target position",
)
def target_set_position(
    session: Any,
    target_name: str,
    mode: str = "geodetic",
    latitude_deg: float | None = None,
    longitude_deg: float | None = None,
    altitude_km: float = 0.0,
    declination_deg: float | None = None,
    right_ascension_deg: float | None = None,
) -> dict[str, Any]:
    target = find_object(session, target_name)
    if str(target.ClassName) != "Target":
        raise StkValidationError(f"{target_name} is not a Target")
    mode = (mode or "geodetic").lower()
    try:
        if mode == "geodetic":
            if latitude_deg is None or longitude_deg is None:
                raise StkValidationError("geodetic mode requires latitude_deg and longitude_deg")
            target.Position.AssignGeodetic(float(latitude_deg), float(longitude_deg), float(altitude_km))
        elif mode == "spherical":
            if declination_deg is None or right_ascension_deg is None:
                raise StkValidationError(
                    "spherical mode requires declination_deg and right_ascension_deg"
                )
            # STK's spherical position uses (declination, right ascension, altitude).
            target.Position.AssignSpherical(
                float(declination_deg), float(right_ascension_deg), float(altitude_km)
            )
        else:
            raise StkValidationError(f"Unknown target position mode: {mode!r}")
        query = None
        try:
            query = list(target.Position.QuerySpherical())
        except Exception:
            pass
    except StkValidationError:
        raise
    except Exception as exc:
        raise wrap_com_error(exc, f"Setting target position for {target_name}") from exc
    return {
        "target": str(target.InstanceName),
        "mode": mode,
        "query_spherical": query,
    }


@tool(
    "target_create",
    "Create a celestial target object (star-like pointing target).",
    object_schema(
        {
            "name": p("string", "Target name"),
            "replace_existing": p("boolean", "Unload an existing target", default=False),
        },
        ["name"],
    ),
    category="objects",
    mutating=True,
    returns="target info",
)
def target_create(session: Any, name: str, replace_existing: bool = False) -> dict[str, Any]:
    target = new_object(session.scenario, "Target", name, replace=replace_existing)
    return object_summary(target)


@tool(
    "sensor_create",
    "Create a sensor on a parent object and configure a simple cone.",
    object_schema(
        {
            "parent_name": p("string", "Parent satellite/facility name"),
            "sensor_name": p("string", "Sensor name"),
            "pattern": p(
                "string",
                "Sensor pattern",
                enum=list(SENSOR_PATTERN),
                default="SimpleCone",
            ),
            "cone_angle_deg": p(
                "number", "Simple-cone half angle (deg)", default=10.0, minimum=0.001, maximum=180
            ),
            "replace_existing": p("boolean", "Unload an existing sensor", default=False),
        },
        ["parent_name", "sensor_name"],
    ),
    category="sensor",
    mutating=True,
    returns="sensor info",
)
def sensor_create(
    session: Any,
    parent_name: str,
    sensor_name: str,
    pattern: str = "SimpleCone",
    cone_angle_deg: float = 10.0,
    replace_existing: bool = False,
) -> dict[str, Any]:
    parent = find_object(session, parent_name)
    sensor_name = validate_name(sensor_name, "sensor name")
    existing = None
    try:
        existing = parent.Children.Item(sensor_name)
    except Exception:
        existing = None
    if existing is not None:
        if not replace_existing:
            raise StkOperationError(f"Sensor '{sensor_name}' already exists on {parent.InstanceName}")
        existing.Unload()
    try:
        sensor = parent.Children.New(OBJECT_TYPE["Sensor"], sensor_name)
        sensor.SetPatternType(sensor_pattern_code(pattern))
        if (pattern or "SimpleCone").lower() == "simplecone":
            sensor.Pattern.ConeAngle = float(cone_angle_deg)
    except Exception as exc:
        raise wrap_com_error(exc, f"Creating sensor {sensor_name}") from exc
    return {
        **object_summary(sensor),
        "parent": str(parent.InstanceName),
        "pattern": pattern,
        "cone_angle_deg": cone_angle_deg if (pattern or "SimpleCone").lower() == "simplecone" else None,
    }


@tool(
    "sensor_set_cone",
    "Set the half-angle of a SimpleCone sensor.",
    object_schema(
        {
            "parent_name": p("string", "Parent object name"),
            "sensor_name": p("string", "Sensor name"),
            "cone_angle_deg": p("number", "Cone half-angle (deg)", minimum=0.001, maximum=180),
        },
        ["parent_name", "sensor_name", "cone_angle_deg"],
    ),
    category="sensor",
    mutating=True,
    returns="sensor info",
)
def sensor_set_cone(
    session: Any, parent_name: str, sensor_name: str, cone_angle_deg: float
) -> dict[str, Any]:
    parent = find_object(session, parent_name)
    try:
        sensor = parent.Children.Item(sensor_name)
    except Exception:
        sensor = find_object(session, sensor_name)
    if str(sensor.ClassName) != "Sensor":
        raise StkValidationError(f"{sensor_name} is not a Sensor")
    try:
        sensor.Pattern.ConeAngle = float(cone_angle_deg)
    except Exception as exc:
        raise wrap_com_error(exc, "Setting sensor cone angle") from exc
    return {**object_summary(sensor), "cone_angle_deg": cone_angle_deg}


@tool(
    "sensor_list",
    "List sensors, optionally limited to one parent object.",
    object_schema({"parent_name": p("string", "Optional parent object name")}),
    category="sensor",
    returns="sensor list",
)
def sensor_list(session: Any, parent_name: str | None = None) -> dict[str, Any]:
    roots = [find_object(session, parent_name)] if parent_name else child_list(session.scenario)
    sensors: list[dict[str, Any]] = []
    stack = list(roots)
    while stack:
        obj = stack.pop()
        if str(getattr(obj, "ClassName", "")) == "Sensor":
            sensors.append(object_summary(obj))
        stack.extend(child_list(obj))
    return {"count": len(sensors), "sensors": sensors}


@tool(
    "constellation_create",
    "Create a constellation and optionally add satellites to it.",
    object_schema(
        {
            "name": p("string", "Constellation name"),
            "objects": p(
                "array",
                "Object names/paths to add",
                items={"type": "string"},
                default=[],
            ),
            "replace_existing": p("boolean", "Unload an existing constellation", default=False),
        },
        ["name"],
    ),
    category="constellation",
    mutating=True,
    returns="constellation info",
)
def constellation_create(
    session: Any, name: str, objects: list[str] | None = None, replace_existing: bool = False
) -> dict[str, Any]:
    constellation = new_object(session.scenario, "Constellation", name, replace=replace_existing)
    added = []
    for object_name in objects or []:
        try:
            constellation.Objects.Add(truncated_path(find_object(session, object_name)))
            added.append(object_name)
        except Exception as exc:
            raise wrap_com_error(exc, f"Adding {object_name} to constellation") from exc
    return {**object_summary(constellation), "members_added": added, "member_count": len(added)}


@tool(
    "constellation_add_object",
    "Add a satellite/object to a constellation.",
    object_schema(
        {
            "constellation_name": p("string", "Constellation name"),
            "object_name": p("string", "Object name or path"),
        },
        ["constellation_name", "object_name"],
    ),
    category="constellation",
    mutating=True,
    returns="constellation info",
)
def constellation_add_object(
    session: Any, constellation_name: str, object_name: str
) -> dict[str, Any]:
    constellation = find_object(session, constellation_name)
    obj = find_object(session, object_name)
    try:
        constellation.Objects.Add(truncated_path(obj))
    except Exception as exc:
        raise wrap_com_error(exc, "Adding constellation member") from exc
    return {
        "constellation": str(constellation.InstanceName),
        "object_added": str(obj.InstanceName),
        "member_count": int(constellation.Objects.Count),
    }


@tool(
    "constellation_list",
    "List constellations and their members.",
    object_schema({}),
    category="constellation",
    returns="constellation list",
)
def constellation_list(session: Any) -> list[dict[str, Any]]:
    rows = []
    sc = session.scenario
    for index in range(int(sc.Children.Count)):
        obj = sc.Children.Item(index)
        if str(obj.ClassName) != "Constellation":
            continue
        members = []
        try:
            for i in range(int(obj.Objects.Count)):
                members.append(str(obj.Objects.Item(i).ObjectName))
        except Exception:
            pass
        rows.append({**object_summary(obj), "members": members})
    return rows


@tool(
    "constellation_build_walker",
    "Batch-build a Walker Delta/Star constellation from circular orbits and add "
    "all generated satellites to a constellation object.",
    object_schema(
        {
            "name": p("string", "Constellation name"),
            "total_sats": p("integer", "Total satellites (1-200)", default=12, minimum=1, maximum=200),
            "planes": p("integer", "Number of orbital planes", default=3, minimum=1, maximum=200),
            "pattern": p(
                "string",
                "Walker pattern: delta (360° RAAN spread) or star (180°)",
                enum=["walker_delta", "walker_star"],
                default="walker_delta",
            ),
            "altitude_km": p("number", "Circular altitude (km)", default=550, minimum=0),
            "inclination_deg": p("number", "Inclination (deg)", default=53, minimum=0, maximum=180),
            "phasing": p("integer", "Walker phasing factor F", default=0, minimum=0, maximum=199),
            "raan0_deg": p("number", "RAAN of the first plane (deg)", default=0),
            "mean_anomaly0_deg": p("number", "Mean anomaly of the first satellite (deg)", default=0),
            "epoch": p("string", "Optional orbit epoch"),
            "propagator": p(
                "string",
                "Propagator",
                enum=["TwoBody", "J2Perturbation", "J4Perturbation", "HPOP"],
                default="TwoBody",
            ),
            "name_prefix": p("string", "Satellite name prefix", default="Sat"),
            "replace_existing": p(
                "boolean", "Unload an existing constellation with this name", default=False
            ),
        },
        ["name", "total_sats", "planes"],
    ),
    category="constellation",
    mutating=True,
    returns="generated constellation",
    tags=["constellation", "walker", "batch"],
)
def constellation_build_walker(
    session: Any,
    name: str,
    total_sats: int = 12,
    planes: int = 3,
    pattern: str = "walker_delta",
    altitude_km: float = 550.0,
    inclination_deg: float = 53.0,
    phasing: int = 0,
    raan0_deg: float = 0.0,
    mean_anomaly0_deg: float = 0.0,
    epoch: str | None = None,
    propagator: str = "TwoBody",
    name_prefix: str = "Sat",
    replace_existing: bool = False,
) -> dict[str, Any]:
    from ..timeutil import format_stk, parse_time

    if not 1 <= total_sats <= 200:
        raise StkValidationError("total_sats must be in [1, 200]")
    if not 1 <= planes <= total_sats:
        raise StkValidationError("planes must be in [1, total_sats]")
    if total_sats % planes:
        raise StkValidationError("total_sats must be divisible by planes")
    if phasing < 0 or phasing >= max(planes, 1):
        raise StkValidationError("phasing must be in [0, planes-1]")
    prefix = validate_name(name_prefix, "name_prefix")
    pattern = (pattern or "walker_delta").lower()
    if pattern not in {"walker_delta", "walker_star"}:
        raise StkValidationError(f"Unknown Walker pattern: {pattern!r}")
    sc = session.scenario
    constellation = new_object(
        sc, "Constellation", name, replace=replace_existing
    )
    per_plane = total_sats // planes
    raan_spread = 360.0 if pattern == "walker_delta" else 180.0
    earth_radius_km = 6378.137
    semi_major_axis = earth_radius_km + float(altitude_km)
    prop_code = propagator_code(propagator)
    epoch_value = format_stk(parse_time(epoch)) if epoch else None
    satellites: list[str] = []
    index = 0
    try:
        for plane in range(planes):
            raan = (float(raan0_deg) + plane * raan_spread / planes) % 360.0
            for slot in range(per_plane):
                index += 1
                sat_name = f"{prefix}{index:02d}"
                satellite = new_object(sc, "Satellite", sat_name)
                satellite.SetPropagatorType(prop_code)
                representation = satellite.Propagator.InitialState.Representation
                if epoch_value:
                    representation.Epoch = epoch_value
                mean_anomaly = (
                    float(mean_anomaly0_deg)
                    + slot * 360.0 / per_plane
                    + phasing * 360.0 / total_sats
                ) % 360.0
                representation.AssignClassical(
                    3,
                    semi_major_axis,
                    0.0,
                    float(inclination_deg),
                    0.0,
                    raan,
                    mean_anomaly,
                )
                satellite.Propagator.Propagate()
                constellation.Objects.Add(f"Satellite/{satellite.InstanceName}")
                satellites.append(str(satellite.InstanceName))
    except Exception as exc:
        raise wrap_com_error(exc, f"Building {pattern} constellation '{name}'") from exc
    return {
        **object_summary(constellation),
        "pattern": pattern,
        "total_sats": total_sats,
        "planes": planes,
        "sats_per_plane": per_plane,
        "phasing": phasing,
        "altitude_km": altitude_km,
        "semi_major_axis_km": semi_major_axis,
        "inclination_deg": inclination_deg,
        "raan_spread_deg": raan_spread,
        "satellites": satellites,
        "member_count": int(constellation.Objects.Count),
    }


@tool(
    "chain_create",
    "Create an access chain and optionally add objects to it.",
    object_schema(
        {
            "name": p("string", "Chain name"),
            "objects": p("array", "Object names/paths", items={"type": "string"}, default=[]),
            "replace_existing": p("boolean", "Unload an existing chain", default=False),
        },
        ["name"],
    ),
    category="chain",
    mutating=True,
    returns="chain info",
)
def chain_create(
    session: Any, name: str, objects: list[str] | None = None, replace_existing: bool = False
) -> dict[str, Any]:
    chain = new_object(session.scenario, "Chain", name, replace=replace_existing)
    added = []
    for object_name in objects or []:
        obj = find_object(session, object_name)
        try:
            chain.Objects.Add(truncated_path(obj))
            added.append(str(obj.InstanceName))
        except Exception as exc:
            raise wrap_com_error(exc, f"Adding {object_name} to chain") from exc
    return {**object_summary(chain), "members_added": added}


@tool(
    "chain_add_object",
    "Append an object to an access chain.",
    object_schema(
        {
            "chain_name": p("string", "Chain name"),
            "object_name": p("string", "Object name or path"),
        },
        ["chain_name", "object_name"],
    ),
    category="chain",
    mutating=True,
    returns="chain info",
)
def chain_add_object(session: Any, chain_name: str, object_name: str) -> dict[str, Any]:
    chain = find_object(session, chain_name)
    obj = find_object(session, object_name)
    try:
        chain.Objects.Add(truncated_path(obj))
    except Exception as exc:
        raise wrap_com_error(exc, "Adding chain member") from exc
    return {"chain": str(chain.InstanceName), "object_added": str(obj.InstanceName)}


@tool(
    "chain_compute_access",
    "Compute access through a chain and return the computed strand intervals.",
    object_schema({"chain_name": p("string", "Chain name")}, ["chain_name"]),
    category="chain",
    mutating=True,
    returns="chain access",
)
def chain_compute_access(session: Any, chain_name: str) -> dict[str, Any]:
    chain = find_object(session, chain_name)
    if str(chain.ClassName) != "Chain":
        raise StkValidationError(f"{chain_name} is not a Chain")
    try:
        chain.ComputeAccess()
    except Exception as exc:
        raise wrap_com_error(exc, "ComputeAccess(chain)") from exc
    from ..stk_common import query_data_provider

    payload: dict[str, Any] = {"chain": str(chain.InstanceName), "computed": True}
    try:
        payload["access_intervals"] = query_data_provider(
            chain,
            "Interval List",
            "CompleteChainAccessIntervals",
            max_rows=1000,
        )
    except Exception as exc:
        payload["access_intervals_error"] = str(exc)
    return payload


@tool(
    "platform_create",
    "Create an aircraft, ship or ground vehicle.",
    object_schema(
        {
            "name": p("string", "Platform name"),
            "platform_type": p(
                "string", "Platform class", enum=["Aircraft", "Ship", "GroundVehicle"]
            ),
            "replace_existing": p("boolean", "Unload an existing platform", default=False),
        },
        ["name", "platform_type"],
    ),
    category="platform",
    mutating=True,
    returns="platform info",
)
def platform_create(
    session: Any, name: str, platform_type: str, replace_existing: bool = False
) -> dict[str, Any]:
    if platform_type not in {"Aircraft", "Ship", "GroundVehicle"}:
        raise StkValidationError(f"Unsupported platform type: {platform_type}")
    platform = new_object(session.scenario, platform_type, name, replace=replace_existing)
    return object_summary(platform)


@tool(
    "platform_list",
    "List aircraft, ships and ground vehicles in the scenario.",
    object_schema({}),
    category="platform",
    returns="platform list",
)
def platform_list(session: Any) -> list[dict[str, Any]]:
    rows = []
    sc = session.scenario
    for index in range(int(sc.Children.Count)):
        obj = sc.Children.Item(index)
        if str(obj.ClassName) in {"Aircraft", "Ship", "GroundVehicle"}:
            rows.append(object_summary(obj))
    return rows


@tool(
    "platform_set_waypoints",
    "Set a time-specified great-arc route for an aircraft, ship or ground vehicle "
    "and propagate it.",
    object_schema(
        {
            "platform_name": p("string", "Platform name"),
            "waypoints": p(
                "array",
                "Waypoints in time order",
                items={
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "time": {"type": "string", "description": "Waypoint time (UTCG/ISO)"},
                        "latitude_deg": {"type": "number", "description": "Latitude (-90..90)"},
                        "longitude_deg": {"type": "number", "description": "Longitude (-180..180)"},
                        "altitude_km": {"type": "number", "description": "Altitude (km)"},
                        "turn_radius_km": {"type": "number", "description": "Turn radius (km)"},
                    },
                    "required": ["time", "latitude_deg", "longitude_deg"],
                },
            ),
        },
        ["platform_name", "waypoints"],
    ),
    category="platform",
    mutating=True,
    returns="route and state",
)
def platform_set_waypoints(
    session: Any, platform_name: str, waypoints: list[dict[str, Any]]
) -> dict[str, Any]:
    from ..timeutil import format_stk, parse_time

    platform = find_object(session, platform_name)
    if str(platform.ClassName) not in {"Aircraft", "Ship", "GroundVehicle"}:
        raise StkValidationError(f"{platform_name} is not an aircraft/ship/ground vehicle")
    if len(waypoints) < 2:
        raise StkValidationError("at least two waypoints are required")
    rows = []
    for waypoint in waypoints:
        rows.append(
            [
                format_stk(parse_time(waypoint["time"])),
                float(waypoint["latitude_deg"]),
                float(waypoint["longitude_deg"]),
                float(waypoint.get("altitude_km", 0.0)),
                float(waypoint.get("turn_radius_km", 0.0)),
            ]
        )
    try:
        route = platform.Route
        route.Method = 2  # specify time at each waypoint
        route.SetPointsSpecifyTimeAndPropagate(rows)
        route.Propagate()
    except Exception as exc:
        raise wrap_com_error(exc, f"Setting route for {platform_name}") from exc
    return {
        "platform": str(platform.InstanceName),
        "waypoint_count": int(route.Waypoints.Count),
        "state": platform_state(session, platform_name),
    }


@tool(
    "platform_state",
    "Query an aircraft/ship/ground-vehicle position at a time.",
    object_schema(
        {
            "platform_name": p("string", "Platform name"),
            "time": p("string", "Query time (defaults to scenario start)"),
        },
        ["platform_name"],
    ),
    category="platform",
    returns="platform state",
)
def platform_state(
    session: Any, platform_name: str, time: str | None = None
) -> dict[str, Any]:
    from ..stk_common import query_data_provider
    from ..timeutil import format_stk, parse_time

    platform = find_object(session, platform_name)
    if str(platform.ClassName) not in {"Aircraft", "Ship", "GroundVehicle"}:
        raise StkValidationError(f"{platform_name} is not a platform")
    query_time = format_stk(
        parse_time(time, default=parse_time(str(session.scenario.StartTime)))
    )
    try:
        return {
            "platform": str(platform.InstanceName),
            "time": query_time,
            "state": query_data_provider(
                platform, "LLA State", "Fixed", time=query_time, max_rows=1
            ),
        }
    except Exception:
        return {
            "platform": str(platform.InstanceName),
            "time": query_time,
            "state": query_data_provider(
                platform, "Cartesian Position", "Fixed", time=query_time, max_rows=1
            ),
        }


@tool(
    "object_set_graphics",
    "Set 2D graphics attributes such as visibility, label, marker and line style.",
    object_schema(
        {
            "object_name": p("string", "Object name"),
            "visible": p("boolean", "Object visibility"),
            "label_visible": p("boolean", "Label visibility"),
            "marker_style": p("string", "Marker style name"),
            "line_style": p("string", "Line style name"),
        },
        ["object_name"],
    ),
    category="graphics",
    mutating=True,
    returns="applied graphics",
)
def object_set_graphics(
    session: Any,
    object_name: str,
    visible: bool | None = None,
    label_visible: bool | None = None,
    marker_style: str | None = None,
    line_style: str | None = None,
) -> dict[str, Any]:
    obj = find_object(session, object_name)
    applied: dict[str, Any] = {}
    errors: list[str] = []
    try:
        graphics = obj.Graphics
    except Exception as exc:
        raise StkOperationError(
            f"Graphics are not available for {object_name}: {exc}"
        ) from exc
    if visible is not None:
        for attr in ("IsObjectGraphicsVisible", "IsVisible"):
            try:
                setattr(graphics, attr, bool(visible))
                applied[attr] = bool(visible)
                break
            except Exception as exc:
                errors.append(f"{attr}: {exc}")
    if label_visible is not None:
        try:
            graphics.LabelVisible = bool(label_visible)
            applied["LabelVisible"] = bool(label_visible)
        except Exception as exc:
            errors.append(f"LabelVisible: {exc}")
    if marker_style:
        try:
            graphics.MarkerStyle = marker_style
            applied["MarkerStyle"] = marker_style
        except Exception as exc:
            errors.append(f"MarkerStyle: {exc}")
    if line_style:
        for attr in ("LineStyle",):
            try:
                setattr(graphics, attr, line_style)
                applied["LineStyle"] = line_style
                break
            except Exception as exc:
                errors.append(f"{attr}: {exc}")
    return {"object": str(obj.InstanceName), "applied": applied, "errors": errors}


@tool(
    "object_get_graphics",
    "Read the main 2D graphics attributes of an object.",
    object_schema({"object_name": p("string", "Object name")}, ["object_name"]),
    category="graphics",
    returns="graphics attributes",
)
def object_get_graphics(session: Any, object_name: str) -> dict[str, Any]:
    obj = find_object(session, object_name)
    try:
        graphics = obj.Graphics
    except Exception as exc:
        raise StkOperationError(f"Graphics are not available for {object_name}: {exc}") from exc
    payload: dict[str, Any] = {"object": str(obj.InstanceName)}
    for attr in ("IsObjectGraphicsVisible", "IsVisible", "LabelVisible", "MarkerStyle", "Color", "LineStyle"):
        try:
            payload[attr] = str(getattr(graphics, attr))
        except Exception:
            payload[attr] = None
    return payload
