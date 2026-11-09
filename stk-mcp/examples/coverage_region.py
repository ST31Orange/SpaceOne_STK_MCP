"""Regional coverage example with a Figure of Merit.

    python examples/coverage_region.py
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
        service.connect()
        service.invoke(
            "scenario_create",
            {
                "name": "Example_Coverage",
                "start_time": "1 Jan 2026 00:00:00.000",
                "stop_time": "1 Jan 2026 06:00:00.000",
                "replace_existing": True,
            },
        )
        service.invoke("satellite_create", {"name": "Sat1", "propagator": "TwoBody"})
        service.invoke(
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
            },
        )
        service.invoke("coverage_create", {"name": "Cov"})
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
        service.invoke("coverage_add_asset", {"coverage_name": "Cov", "object_name": "Sat1"})
        computed = service.invoke("coverage_compute", {"coverage_name": "Cov"})
        print(json.dumps(computed["statistics"], indent=2, ensure_ascii=False))
        fom = service.invoke(
            "coverage_fom_create",
            {"coverage_name": "Cov", "name": "FOM_Revisit", "definition_type": 10},
        )
        print("FOM:", fom["name"], fom["definition_type"])
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
