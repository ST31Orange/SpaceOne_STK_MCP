"""Antenna, receiver, transmitter and radar equipment operations."""

from __future__ import annotations

from typing import Any

from ..enums import OBJECT_TYPE
from ..errors import StkNotFoundError, StkOperationError, StkValidationError, wrap_com_error
from ..stk_common import child_list, find_object, object_summary, validate_name
from ..tooling import object_schema, p, tool

_EQUIPMENT_TYPES = {
    "Antenna": OBJECT_TYPE["Antenna"],
    "Receiver": OBJECT_TYPE["Receiver"],
    "Transmitter": OBJECT_TYPE["Transmitter"],
    "Radar": OBJECT_TYPE["Radar"],
}
_EQUIPMENT_CLASSES = set(_EQUIPMENT_TYPES)


def _equipment(session: Any, parent_name: str, equipment_name: str) -> tuple[Any, Any]:
    parent = find_object(session, parent_name)
    try:
        equipment = parent.Children.Item(equipment_name)
    except Exception as exc:
        raise StkNotFoundError(
            f"Equipment '{equipment_name}' was not found on '{parent_name}'"
        ) from exc
    if str(equipment.ClassName) not in _EQUIPMENT_CLASSES:
        raise StkValidationError(f"'{equipment_name}' is not antenna/receiver/transmitter/radar")
    return parent, equipment


@tool(
    "equipment_create",
    "Create an antenna, receiver, transmitter or radar on a parent object.",
    object_schema(
        {
            "parent_name": p("string", "Parent satellite/facility/aircraft name"),
            "name": p("string", "Equipment name"),
            "equipment_type": p(
                "string",
                "Equipment class",
                enum=list(_EQUIPMENT_TYPES),
                default="Transmitter",
            ),
            "model": p("string", "Optional STK model name, e.g. 'Simple Transmitter Model'"),
            "replace_existing": p("boolean", "Unload an existing equipment with this name", default=False),
        },
        ["parent_name", "name"],
    ),
    category="equipment",
    mutating=True,
    returns="equipment info",
    tags=["equipment", "comm"],
)
def equipment_create(
    session: Any,
    parent_name: str,
    name: str,
    equipment_type: str = "Transmitter",
    model: str | None = None,
    replace_existing: bool = False,
) -> dict[str, Any]:
    parent = find_object(session, parent_name)
    name = validate_name(name, "equipment name")
    if equipment_type not in _EQUIPMENT_TYPES:
        raise StkValidationError(
            f"Unknown equipment type: {equipment_type!r}",
            details={"allowed": sorted(_EQUIPMENT_TYPES)},
        )
    existing = None
    try:
        existing = parent.Children.Item(name)
    except Exception:
        existing = None
    if existing is not None:
        if not replace_existing:
            raise StkOperationError(f"'{name}' already exists on '{parent.InstanceName}'")
        existing.Unload()
    try:
        equipment = parent.Children.New(_EQUIPMENT_TYPES[equipment_type], name)
        if model:
            equipment.SetModel(model)
    except Exception as exc:
        raise wrap_com_error(exc, f"Creating {equipment_type} '{name}'") from exc
    payload = {
        **object_summary(equipment),
        "equipment_type": str(equipment.ClassName),
        "parent": str(parent.InstanceName),
    }
    try:
        payload["model"] = str(equipment.Model.Name)
    except Exception:
        payload["model"] = None
    return payload


@tool(
    "equipment_list",
    "List antennas, receivers, transmitters and radars on a parent object.",
    object_schema({"parent_name": p("string", "Parent object name")}, ["parent_name"]),
    category="equipment",
    returns="equipment list",
)
def equipment_list(session: Any, parent_name: str) -> dict[str, Any]:
    parent = find_object(session, parent_name)
    rows = []
    for child in child_list(parent):
        if str(child.ClassName) in _EQUIPMENT_CLASSES:
            row = object_summary(child)
            try:
                row["model"] = str(child.Model.Name)
            except Exception:
                row["model"] = None
            rows.append(row)
    return {"parent": str(parent.InstanceName), "count": len(rows), "equipment": rows}


@tool(
    "equipment_delete",
    "Delete an antenna/receiver/transmitter/radar from its parent.",
    object_schema(
        {
            "parent_name": p("string", "Parent object name"),
            "name": p("string", "Equipment name"),
        },
        ["parent_name", "name"],
    ),
    category="equipment",
    mutating=True,
    returns="delete result",
)
def equipment_delete(session: Any, parent_name: str, name: str) -> dict[str, Any]:
    parent, equipment = _equipment(session, parent_name, name)
    try:
        equipment.Unload()
    except Exception as exc:
        raise wrap_com_error(exc, f"Unloading equipment '{name}'") from exc
    return {"parent": str(parent.InstanceName), "deleted": name}


@tool(
    "equipment_configure",
    "Configure a transmitter (frequency/EIRP/data rate), antenna (design frequency/"
    "diameter) or receiver (G/T). Only writable model properties are applied; "
    "unsupported fields are returned in errors.",
    object_schema(
        {
            "parent_name": p("string", "Parent object name"),
            "name": p("string", "Equipment name"),
            "model": p("string", "Optional STK model name"),
            "frequency_mhz": p("number", "Transmitter/antenna frequency (MHz)"),
            "bandwidth_hz": p("number", "Receiver bandwidth (Hz)"),
            "g_over_t_db_k": p("number", "Receiver G/T (dB/K)"),
            "eirp_dbw": p("number", "Transmitter EIRP (dBW)"),
            "data_rate_bps": p("number", "Transmitter data rate (bps)"),
            "diameter_m": p("number", "Antenna diameter (m)"),
            "efficiency": p("number", "Antenna efficiency (0-1)", minimum=0, maximum=1),
        },
        ["parent_name", "name"],
    ),
    category="equipment",
    mutating=True,
    returns="applied/readback values",
)
def equipment_configure(
    session: Any,
    parent_name: str,
    name: str,
    model: str | None = None,
    frequency_mhz: float | None = None,
    bandwidth_hz: float | None = None,
    g_over_t_db_k: float | None = None,
    eirp_dbw: float | None = None,
    data_rate_bps: float | None = None,
    diameter_m: float | None = None,
    efficiency: float | None = None,
) -> dict[str, Any]:
    _, equipment = _equipment(session, parent_name, name)
    equipment_type = str(equipment.ClassName)
    applied: dict[str, Any] = {}
    errors: list[str] = []

    def apply(attr: str, value: Any) -> None:
        if value is None:
            return
        try:
            setattr(equipment.Model, attr, value)
            applied[attr] = value
        except Exception as exc:
            errors.append(f"{attr}: {exc}")

    try:
        if model:
            equipment.SetModel(model)
        if equipment_type == "Transmitter":
            if frequency_mhz is not None:
                apply("Frequency", float(frequency_mhz) / 1000.0)  # STK default: GHz
            apply("Eirp", eirp_dbw)
            apply("DataRate", data_rate_bps)
        elif equipment_type == "Antenna":
            if frequency_mhz is not None:
                apply("DesignFrequency", float(frequency_mhz) / 1000.0)
            apply("Diameter", diameter_m)
            apply("Efficiency", efficiency)
        elif equipment_type == "Receiver":
            apply("GOverT", g_over_t_db_k)
            if bandwidth_hz is not None:
                apply("Bandwidth", float(bandwidth_hz) / 1e6)  # STK default: MHz
            if frequency_mhz is not None:
                apply("Frequency", float(frequency_mhz) / 1000.0)
        else:
            errors.append("Radar model configuration is not exposed by this tool")
    except Exception as exc:
        raise wrap_com_error(exc, f"Configuring {equipment_type} '{name}'") from exc

    readback: dict[str, Any] = {}
    for attr in ("Frequency", "Bandwidth", "GOverT", "Eirp", "DataRate", "DesignFrequency", "Diameter", "Efficiency"):
        try:
            readback[attr] = getattr(equipment.Model, attr)
        except Exception:
            continue
    try:
        readback["Model"] = str(equipment.Model.Name)
    except Exception:
        pass
    return {
        "parent": str(parent_name),
        "equipment": name,
        "equipment_type": equipment_type,
        "applied": applied,
        "readback": readback,
        "errors": errors,
    }
