from __future__ import annotations

import os

import pytest

from spaceone_stk_mcp.config import Settings
from spaceone_stk_mcp.errors import StkMcpError
from spaceone_stk_mcp.service import StkService

pytestmark = [
    pytest.mark.stk,
    pytest.mark.skipif(
        os.getenv("STK_MCP_RUN_INTEGRATION") != "1",
        reason="set STK_MCP_RUN_INTEGRATION=1 to launch local STK",
    ),
]


def test_end_to_end_stk_workflow(tmp_path):
    settings = Settings.from_env()
    settings.stk_visible = False
    settings.stk_user_control = False
    settings.attach_existing = False
    service = StkService(settings)
    try:
        status = service.connect()
        assert status["connected"] is True
        assert status["prog_id"].startswith("STK")

        scenario = service.invoke(
            "scenario_create",
            {
                "name": "IT_Pytest",
                "start_time": "1 Jan 2026 00:00:00.000",
                "stop_time": "1 Jan 2026 06:00:00.000",
                "replace_existing": True,
            },
        )
        assert scenario["name"] == "IT_Pytest"

        service.invoke(
            "satellite_create", {"name": "Sat1", "propagator": "TwoBody"}
        )
        orbit = service.invoke(
            "satellite_set_orbit",
            {
                "satellite_name": "Sat1",
                "mode": "classical",
                "semi_major_axis_km": 7000.0,
                "eccentricity": 0.001,
                "inclination_deg": 97.4,
                "raan_deg": 10.0,
                "arg_of_perigee_deg": 0.0,
                "mean_anomaly_deg": 45.0,
                "epoch": "1 Jan 2026 00:00:00.000",
            },
        )
        assert orbit["state"]["position"]["x"]

        state = service.invoke(
            "satellite_state",
            {"satellite_name": "Sat1", "time": "1 Jan 2026 01:00:00.000"},
        )
        assert state["position"]["x"]
        assert state["velocity"]["x"]
        assert state["lla"]["Lat"] is not None

        service.invoke(
            "facility_create",
            {"name": "Fac", "latitude_deg": 40.0, "longitude_deg": 116.0},
        )
        access = service.invoke(
            "access_compute", {"from_object": "Sat1", "to_object": "Fac"}
        )
        assert access["access_count"] >= 1
        assert access["intervals"][0]["start_iso"].endswith("Z")

        coverage = service.invoke("coverage_create", {"name": "Cov"})
        assert coverage["class_name"] == "CoverageDefinition"
        service.invoke(
            "coverage_set_grid",
            {
                "coverage_name": "Cov",
                "mode": "lat_lon_region",
                "min_lat": 30,
                "max_lat": 50,
                "min_lon": 100,
                "max_lon": 130,
                "lat_resolution_deg": 4,
                "lon_resolution_deg": 4,
            },
        )
        service.invoke(
            "coverage_add_asset", {"coverage_name": "Cov", "object_name": "Sat1"}
        )
        computed = service.invoke("coverage_compute", {"coverage_name": "Cov"})
        assert computed["computed"] is True
        assert "Coverage Definition" in computed["statistics"]

        tx = service.invoke(
            "equipment_create",
            {"parent_name": "Sat1", "name": "Tx1", "equipment_type": "Transmitter"},
        )
        assert tx["equipment_type"] == "Transmitter"
        tx_config = service.invoke(
            "equipment_configure",
            {
                "parent_name": "Sat1",
                "name": "Tx1",
                "frequency_mhz": 2200,
                "eirp_dbw": 12,
                "data_rate_bps": 1_000_000,
            },
        )
        assert tx_config["readback"]["Frequency"] == 2.2
        service.invoke(
            "equipment_create",
            {"parent_name": "Fac", "name": "Rx1", "equipment_type": "Receiver"},
        )
        equipment = service.invoke("equipment_list", {"parent_name": "Sat1"})
        assert equipment["count"] >= 1

        aircraft = service.invoke(
            "platform_create", {"name": "Aircraft1", "platform_type": "Aircraft"}
        )
        assert aircraft["class_name"] == "Aircraft"
        route = service.invoke(
            "platform_set_waypoints",
            {
                "platform_name": "Aircraft1",
                "waypoints": [
                    {
                        "time": "1 Jan 2026 00:00:00.000",
                        "latitude_deg": 40,
                        "longitude_deg": 116,
                        "altitude_km": 1,
                    },
                    {
                        "time": "1 Jan 2026 00:30:00.000",
                        "latitude_deg": 41,
                        "longitude_deg": 117,
                        "altitude_km": 1,
                    },
                ],
            },
        )
        assert route["waypoint_count"] == 2
        assert abs(route["state"]["state"]["rows"][0]["Lat"] - 40.0) < 1e-6

        area = service.invoke("area_target_create", {"name": "Poly1"})
        assert area["class_name"] == "AreaTarget"
        polygon = service.invoke(
            "area_target_set_polygon",
            {
                "area_target_name": "Poly1",
                "points": [
                    {"latitude_deg": 40, "longitude_deg": 116},
                    {"latitude_deg": 41, "longitude_deg": 116},
                    {"latitude_deg": 41, "longitude_deg": 117},
                    {"latitude_deg": 40, "longitude_deg": 117},
                ],
            },
        )
        assert polygon["point_count"] == 4

        service.invoke("target_create", {"name": "Tgt1"})
        target = service.invoke(
            "target_set_position",
            {
                "target_name": "Tgt1",
                "mode": "spherical",
                "declination_deg": 30,
                "right_ascension_deg": 120,
            },
        )
        assert target["query_spherical"][0] > 29

        service.invoke("chain_create", {"name": "Ch1", "objects": ["Sat1", "Fac"]})
        chain = service.invoke("chain_compute_access", {"chain_name": "Ch1"})
        assert chain["computed"] is True
        assert chain["access_intervals"]["row_count"] >= 1

        styles = service.invoke("report_list_styles", {"category": "Access"})
        assert styles["count"] >= 1
        assert any(item["name"] == "Access" for item in styles["styles"])
        with pytest.raises(StkMcpError) as bad_style:
            service.invoke(
                "report_create",
                {"object_name": "Sat1", "style": "No Such Style"},
            )
        assert bad_style.value.code == "INVALID_ARGS"
        with pytest.raises(StkMcpError) as bad_coverage_style:
            service.invoke(
                "report_create",
                {"object_name": "Cov", "style": "Coverage"},
            )
        assert bad_coverage_style.value.code == "INVALID_ARGS"
        assert "available_styles" in (bad_coverage_style.value.details or {})

        walker = service.invoke(
            "constellation_build_walker",
            {
                "name": "WalkerTest",
                "total_sats": 6,
                "planes": 3,
                "altitude_km": 550,
                "inclination_deg": 53,
                "phasing": 1,
            },
        )
        assert walker["member_count"] == 6
        assert len(walker["satellites"]) == 6

        service.invoke(
            "satellite_create", {"name": "Astro1", "propagator": "Astrogator"}
        )
        astrogator = service.invoke("astrogator_summary", {"satellite_name": "Astro1"})
        assert astrogator["segment_count"] >= 2
        astrogator_run = service.invoke("astrogator_run", {"satellite_name": "Astro1"})
        assert astrogator_run["run"] is True

        report = service.invoke(
            "report_create",
            {
                "object_name": "Sat1",
                "style": "Access",
                "access_object": "Fac",
                "file_path": str(tmp_path / "access.txt"),
            },
        )
        assert report["exists"] is True
        assert report["size"] > 0
        assert "Access" in report["preview"]

        # SGP4/TLE path through the Connect socket.
        service.invoke(
            "satellite_create", {"name": "TleSat", "propagator": "SGP4"}
        )
        service.invoke(
            "satellite_set_orbit",
            {
                "satellite_name": "TleSat",
                "mode": "tle",
                "tle_line1": "1 25544U 98067A   26001.00000000  .00000000  00000-0  00000-0 0  9999",
                "tle_line2": "2 25544  51.6400 100.0000 0005000  50.0000 310.0000 15.50000000 00004",
            },
        )
        tle_state = service.invoke(
            "satellite_state",
            {"satellite_name": "TleSat", "time": "1 Jan 2026 01:00:00.000"},
        )
        assert tle_state["position"].get("x") is not None
        tle_summary = service.invoke(
            "satellite_tle_summary", {"satellite_name": "TleSat"}
        )
        assert "columns" in tle_summary

        saved = service.invoke(
            "scenario_save",
            {"path": str(tmp_path / "scenario" / "it.sc"), "confirm_save": True},
        )
        assert saved["status"] == "saved"
        with pytest.raises(StkMcpError) as no_confirm:
            service.invoke("scenario_save", {"path": str(tmp_path / "it2.sc")})
        assert no_confirm.value.code == "SAVE_CONFIRMATION_REQUIRED"
        with pytest.raises(StkMcpError) as chinese_path:
            service.invoke(
                "scenario_save",
                {"path": str(tmp_path / "场景.sc"), "confirm_save": True},
            )
        assert chinese_path.value.code == "INVALID_ARGS"
        service.invoke("scenario_close", {})
        opened = service.invoke("scenario_open", {"path": str(tmp_path / "scenario" / "it.sc")})
        assert opened["name"].lower() == "it"
        assert opened["object_count"] >= 3
    finally:
        try:
            service.invoke("scenario_close", {})
        except Exception:
            pass
        try:
            service.disconnect(quit=False, close_scenario=False)
        except Exception:
            pass
        service.close()
