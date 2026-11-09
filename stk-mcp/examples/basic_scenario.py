"""Create a scenario, satellite and orbit through the Python service.

Run from the stk-mcp directory:

    python examples/basic_scenario.py
"""

from __future__ import annotations

import json

from spaceone_stk_mcp.config import Settings
from spaceone_stk_mcp.service import StkService


def main() -> int:
    settings = Settings.from_env()
    settings.stk_visible = False
    service = StkService(settings)
    try:
        print("connect:", service.connect())
        print(
            "scenario:",
            service.invoke(
                "scenario_create",
                {
                    "name": "Example_Basic",
                    "start_time": "1 Jan 2026 00:00:00.000",
                    "stop_time": "2 Jan 2026 00:00:00.000",
                    "replace_existing": True,
                },
            )["name"],
        )
        service.invoke("satellite_create", {"name": "Sat1", "propagator": "TwoBody"})
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
        state = service.invoke(
            "satellite_state",
            {"satellite_name": "Sat1", "time": "1 Jan 2026 01:00:00.000"},
        )
        print(json.dumps({"orbit": orbit["mode"], "position": state["position"]}, indent=2))
        return 0
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


if __name__ == "__main__":
    raise SystemExit(main())
