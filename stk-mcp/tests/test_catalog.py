from __future__ import annotations

from spaceone_stk_mcp.registry import catalog, schemas
from spaceone_stk_mcp.tooling import TOOLS


def test_catalog_is_non_empty_and_unique():
    tools = schemas()
    assert len(tools) >= 50
    names = [item["name"] for item in tools]
    assert len(names) == len(set(names))
    assert "satellite_set_orbit" in names
    assert "access_compute" in names
    assert "coverage_compute" in names
    assert "stk_selftest" in names
    for extra in (
        "equipment_create",
        "equipment_configure",
        "platform_set_waypoints",
        "area_target_set_polygon",
        "target_set_position",
        "chain_compute_access",
        "satellite_tle_summary",
    ):
        assert extra in names


def test_every_tool_has_json_schema_parameters():
    for item in schemas():
        assert item["name"]
        assert item["description"]
        schema = item["inputSchema"]
        assert schema["type"] == "object"
        assert isinstance(schema["properties"], dict)
        assert schema.get("additionalProperties") is False
        for required in schema.get("required", []):
            assert required in schema["properties"]


def test_catalog_metadata():
    data = catalog()
    assert data["product"] == "spaceone-stk-mcp"
    assert data["tool_count"] == len(TOOLS)
    assert "satellite" in data["categories"]
    assert "coverage" in data["categories"]
    assert len(data["tools"]) == data["tool_count"]
