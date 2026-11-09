from __future__ import annotations

from fastapi.testclient import TestClient

from spaceone_stk_mcp.config import Settings
from spaceone_stk_mcp.http_server import create_app


def _client() -> TestClient:
    settings = Settings()
    settings.auto_connect = False
    return TestClient(create_app(settings=settings))


def test_health_and_version():
    with _client() as client:
        health = client.get("/health").json()
        assert health["ok"] is True
        assert health["service"] == "spaceone-stk-mcp"
        assert health["connected"] is False
        version = client.get("/api/v1/version").json()
        assert version["data"]["product"] == "spaceone-stk-mcp"
        assert version["data"]["tool_count"] >= 50


def test_tools_catalog_and_detail():
    with _client() as client:
        data = client.get("/api/v1/tools").json()["data"]
        assert data["tool_count"] == len(data["tools"])
        detail = client.get("/api/v1/tools/satellite_set_orbit").json()["data"]
        assert detail["name"] == "satellite_set_orbit"
        assert detail["parameters"]["type"] == "object"


def test_call_status_tool_without_stk():
    with _client() as client:
        response = client.post("/api/v1/tools/stk_status", json={"arguments": {}})
        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"]["connected"] is False


def test_unknown_tool_is_structured_error():
    with _client() as client:
        response = client.post("/api/v1/tools/not_a_tool", json={"arguments": {}})
        assert response.status_code == 400
        error = response.json()["error"]
        assert error["code"] == "INVALID_ARGS"
        assert "not_a_tool" in error["message"]


def test_not_connected_error_is_503():
    with _client() as client:
        response = client.post("/api/v1/tools/scenario_info", json={"arguments": {}})
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "STK_NOT_CONNECTED"
