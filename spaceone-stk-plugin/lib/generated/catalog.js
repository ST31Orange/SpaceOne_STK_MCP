export const CURATED_TOOLS = [
    {
        "name": "stk_connect",
        "operation": "stk_connect",
        "description": "Launch or attach to STK 11/12 through COM. Existing instances are reused; a new instance is started only when no STK automation object is running.",
        "parameters": {
            "type": "object",
            "properties": {
                "prog_id": {
                    "type": "string",
                    "description": "STK ProgID. Omit to use auto-detection (STK 11 preferred, then STK 12).",
                    "enum": [
                        "STK11.Application",
                        "STK12.Application"
                    ]
                },
                "visible": {
                    "type": "boolean",
                    "description": "Show the STK desktop window (headed mode)",
                    "default": true
                },
                "user_control": {
                    "type": "boolean",
                    "description": "Allow the user to interact with STK",
                    "default": true
                },
                "force": {
                    "type": "boolean",
                    "description": "Reconnect even if a session is already active",
                    "default": false
                }
            },
            "additionalProperties": false
        },
        "category": "connection",
        "mutating": true
    },
    {
        "name": "stk_status",
        "operation": "stk_status",
        "description": "Report whether the kernel is connected, the STK version/PID and the open scenario.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": false
        },
        "category": "connection",
        "mutating": false
    },
    {
        "name": "stk_scenario_create",
        "operation": "scenario_create",
        "description": "Create a new STK scenario. Closes the open scenario only when replace_existing=true; otherwise it fails rather than silently discarding work.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Scenario name"
                },
                "start_time": {
                    "type": "string",
                    "description": "Start epoch (ISO-8601 or STK UTCG). Defaults to the current UTC minute."
                },
                "stop_time": {
                    "type": "string",
                    "description": "Stop epoch (ISO-8601 or STK UTCG)"
                },
                "duration_hours": {
                    "type": "number",
                    "description": "Duration used when stop_time is omitted",
                    "default": 24.0
                },
                "description": {
                    "type": "string",
                    "description": "Optional scenario description"
                },
                "path": {
                    "type": "string",
                    "description": "Optional .sc path. Saving requires confirm_save=true and an ASCII-only path."
                },
                "confirm_save": {
                    "type": "boolean",
                    "description": "Explicit user approval to save; never set true without asking the user",
                    "default": false
                },
                "replace_existing": {
                    "type": "boolean",
                    "description": "Close an already-open scenario first",
                    "default": false
                }
            },
            "additionalProperties": false,
            "required": [
                "name"
            ]
        },
        "category": "scenario",
        "mutating": true
    },
    {
        "name": "stk_scenario_info",
        "operation": "scenario_info",
        "description": "Return the current scenario name, time period, duration and top-level objects.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": false
        },
        "category": "scenario",
        "mutating": false
    },
    {
        "name": "stk_scenario_set_time",
        "operation": "scenario_set_time",
        "description": "Update the scenario start/stop time (or extend by duration_hours).",
        "parameters": {
            "type": "object",
            "properties": {
                "start_time": {
                    "type": "string",
                    "description": "New start epoch"
                },
                "stop_time": {
                    "type": "string",
                    "description": "New stop epoch"
                },
                "duration_hours": {
                    "type": "number",
                    "description": "Duration from start when stop is omitted"
                }
            },
            "additionalProperties": false
        },
        "category": "scenario",
        "mutating": true
    },
    {
        "name": "stk_satellite_create",
        "operation": "satellite_create",
        "description": "Create a satellite in the current scenario and select a propagator.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Satellite name"
                },
                "propagator": {
                    "type": "string",
                    "description": "Propagator type",
                    "enum": [
                        "TwoBody",
                        "J2Perturbation",
                        "J4Perturbation",
                        "HPOP",
                        "SGP4",
                        "Astrogator",
                        "StkExternal"
                    ],
                    "default": "TwoBody"
                },
                "replace_existing": {
                    "type": "boolean",
                    "description": "Unload an existing satellite with the same name",
                    "default": false
                }
            },
            "additionalProperties": false,
            "required": [
                "name"
            ]
        },
        "category": "satellite",
        "mutating": true
    },
    {
        "name": "stk_satellite_set_orbit",
        "operation": "satellite_set_orbit",
        "description": "Define a satellite orbit from classical elements, a Cartesian state, TLE lines, or an ephemeris file, then propagate it.",
        "parameters": {
            "type": "object",
            "properties": {
                "satellite_name": {
                    "type": "string",
                    "description": "Satellite name"
                },
                "mode": {
                    "type": "string",
                    "description": "Orbit representation",
                    "enum": [
                        "classical",
                        "cartesian",
                        "tle",
                        "from_file"
                    ],
                    "default": "classical"
                },
                "semi_major_axis_km": {
                    "type": "number",
                    "description": "Classical: semi-major axis (km)",
                    "minimum": 1
                },
                "eccentricity": {
                    "type": "number",
                    "description": "Classical: eccentricity (0-1)",
                    "minimum": 0,
                    "maximum": 0.999999
                },
                "inclination_deg": {
                    "type": "number",
                    "description": "Classical: inclination (deg)",
                    "minimum": 0,
                    "maximum": 180
                },
                "raan_deg": {
                    "type": "number",
                    "description": "Classical: right ascension of ascending node (deg)"
                },
                "arg_of_perigee_deg": {
                    "type": "number",
                    "description": "Classical: argument of perigee (deg)"
                },
                "mean_anomaly_deg": {
                    "type": "number",
                    "description": "Classical: mean anomaly at epoch (deg)"
                },
                "epoch": {
                    "type": "string",
                    "description": "Orbit epoch (IO-8601 or STK UTCG)"
                },
                "coordinate_system": {
                    "type": "string",
                    "description": "Classical/Cartesian coordinate system",
                    "enum": [
                        "AlignmentAtEpoch",
                        "B1950",
                        "Fixed",
                        "J2000",
                        "MeanOfDate",
                        "MeanOfEpoch",
                        "TEMEOfDate",
                        "TEMEOfEpoch",
                        "TrueOfDate",
                        "TrueOfEpoch",
                        "TrueOfRefDate",
                        "ICRF"
                    ],
                    "default": "J2000"
                },
                "x_km": {
                    "type": "number",
                    "description": "Cartesian: X position (km)"
                },
                "y_km": {
                    "type": "number",
                    "description": "Cartesian: Y position (km)"
                },
                "z_km": {
                    "type": "number",
                    "description": "Cartesian: Z position (km)"
                },
                "vx_km_s": {
                    "type": "number",
                    "description": "Cartesian: X velocity (km/s)"
                },
                "vy_km_s": {
                    "type": "number",
                    "description": "Cartesian: Y velocity (km/s)"
                },
                "vz_km_s": {
                    "type": "number",
                    "description": "Cartesian: Z velocity (km/s)"
                },
                "tle_line1": {
                    "type": "string",
                    "description": "TLE: line 1"
                },
                "tle_line2": {
                    "type": "string",
                    "description": "TLE: line 2"
                },
                "file_path": {
                    "type": "string",
                    "description": "From-file: ephemeris file path"
                },
                "propagate": {
                    "type": "boolean",
                    "description": "Propagate after assigning the state",
                    "default": true
                }
            },
            "additionalProperties": false,
            "required": [
                "satellite_name"
            ]
        },
        "category": "satellite",
        "mutating": true
    },
    {
        "name": "stk_satellite_state",
        "operation": "satellite_state",
        "description": "Query a satellite's Cartesian position/velocity, LLA and classical elements at a specific time or at the scenario start.",
        "parameters": {
            "type": "object",
            "properties": {
                "satellite_name": {
                    "type": "string",
                    "description": "Satellite name"
                },
                "time": {
                    "type": "string",
                    "description": "Query time (defaults to scenario start)"
                },
                "frame": {
                    "type": "string",
                    "description": "Cartesian frame group",
                    "enum": [
                        "ICRF",
                        "J2000",
                        "Fixed",
                        "TrueOfDate",
                        "MeanOfDate"
                    ],
                    "default": "ICRF"
                }
            },
            "additionalProperties": false,
            "required": [
                "satellite_name"
            ]
        },
        "category": "analysis",
        "mutating": false
    },
    {
        "name": "stk_satellite_ephemeris",
        "operation": "satellite_ephemeris",
        "description": "Sample a satellite ephemeris over an interval and optionally write a CSV file.",
        "parameters": {
            "type": "object",
            "properties": {
                "satellite_name": {
                    "type": "string",
                    "description": "Satellite name"
                },
                "start_time": {
                    "type": "string",
                    "description": "Start time (defaults to scenario start)"
                },
                "stop_time": {
                    "type": "string",
                    "description": "Stop time (defaults to scenario stop)"
                },
                "step_sec": {
                    "type": "number",
                    "description": "Sampling step in seconds",
                    "default": 60
                },
                "frame": {
                    "type": "string",
                    "description": "Cartesian frame group",
                    "enum": [
                        "ICRF",
                        "J2000",
                        "Fixed",
                        "TrueOfDate",
                        "MeanOfDate"
                    ],
                    "default": "ICRF"
                },
                "include_lla": {
                    "type": "boolean",
                    "description": "Also include LLA columns",
                    "default": true
                },
                "output_path": {
                    "type": "string",
                    "description": "Optional CSV output path"
                },
                "max_rows": {
                    "type": "integer",
                    "description": "Maximum returned rows",
                    "default": 2000
                }
            },
            "additionalProperties": false,
            "required": [
                "satellite_name"
            ]
        },
        "category": "analysis",
        "mutating": false
    },
    {
        "name": "stk_facility_create",
        "operation": "facility_create",
        "description": "Create a ground facility at a geodetic position.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Facility name"
                },
                "latitude_deg": {
                    "type": "number",
                    "description": "Latitude (-90..90)",
                    "minimum": -90,
                    "maximum": 90
                },
                "longitude_deg": {
                    "type": "number",
                    "description": "Longitude (-180..180)",
                    "minimum": -180,
                    "maximum": 180
                },
                "altitude_km": {
                    "type": "number",
                    "description": "Altitude above the ellipsoid (km)",
                    "default": 0.0
                },
                "replace_existing": {
                    "type": "boolean",
                    "description": "Unload an existing facility with this name",
                    "default": false
                }
            },
            "additionalProperties": false,
            "required": [
                "name",
                "latitude_deg",
                "longitude_deg"
            ]
        },
        "category": "objects",
        "mutating": true
    },
    {
        "name": "stk_sensor_create",
        "operation": "sensor_create",
        "description": "Create a sensor on a parent object and configure a simple cone.",
        "parameters": {
            "type": "object",
            "properties": {
                "parent_name": {
                    "type": "string",
                    "description": "Parent satellite/facility name"
                },
                "sensor_name": {
                    "type": "string",
                    "description": "Sensor name"
                },
                "pattern": {
                    "type": "string",
                    "description": "Sensor pattern",
                    "enum": [
                        "ComplexConic",
                        "Custom",
                        "HalfPower",
                        "Rectangular",
                        "SAR",
                        "SimpleCone",
                        "EOIR"
                    ],
                    "default": "SimpleCone"
                },
                "cone_angle_deg": {
                    "type": "number",
                    "description": "Simple-cone half angle (deg)",
                    "default": 10.0,
                    "minimum": 0.001,
                    "maximum": 180
                },
                "replace_existing": {
                    "type": "boolean",
                    "description": "Unload an existing sensor",
                    "default": false
                }
            },
            "additionalProperties": false,
            "required": [
                "parent_name",
                "sensor_name"
            ]
        },
        "category": "sensor",
        "mutating": true
    },
    {
        "name": "stk_access_compute",
        "operation": "access_compute",
        "description": "Compute access intervals between two objects over the scenario interval.",
        "parameters": {
            "type": "object",
            "properties": {
                "from_object": {
                    "type": "string",
                    "description": "Source object name"
                },
                "to_object": {
                    "type": "string",
                    "description": "Target object name"
                },
                "time_step_sec": {
                    "type": "number",
                    "description": "Access computation time step (seconds)"
                }
            },
            "additionalProperties": false,
            "required": [
                "from_object",
                "to_object"
            ]
        },
        "category": "access",
        "mutating": true
    },
    {
        "name": "stk_coverage_create",
        "operation": "coverage_create",
        "description": "Create a coverage definition.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Coverage definition name"
                },
                "replace_existing": {
                    "type": "boolean",
                    "description": "Unload an existing coverage definition",
                    "default": false
                }
            },
            "additionalProperties": false,
            "required": [
                "name"
            ]
        },
        "category": "coverage",
        "mutating": true
    },
    {
        "name": "stk_coverage_set_grid",
        "operation": "coverage_set_grid",
        "description": "Set a global or latitude/longitude coverage grid.",
        "parameters": {
            "type": "object",
            "properties": {
                "coverage_name": {
                    "type": "string",
                    "description": "Coverage definition name"
                },
                "mode": {
                    "type": "string",
                    "description": "Grid bounds",
                    "enum": [
                        "global",
                        "lat_lon_region",
                        "lat_band"
                    ],
                    "default": "global"
                },
                "min_lat": {
                    "type": "number",
                    "description": "Region minimum latitude",
                    "minimum": -90,
                    "maximum": 90
                },
                "max_lat": {
                    "type": "number",
                    "description": "Region maximum latitude",
                    "minimum": -90,
                    "maximum": 90
                },
                "min_lon": {
                    "type": "number",
                    "description": "Region minimum longitude",
                    "minimum": -180,
                    "maximum": 180
                },
                "max_lon": {
                    "type": "number",
                    "description": "Region maximum longitude",
                    "minimum": -180,
                    "maximum": 180
                },
                "lat_resolution_deg": {
                    "type": "number",
                    "description": "Latitude resolution (deg)",
                    "default": 5.0
                },
                "lon_resolution_deg": {
                    "type": "number",
                    "description": "Longitude resolution (deg)",
                    "default": 5.0
                }
            },
            "additionalProperties": false,
            "required": [
                "coverage_name"
            ]
        },
        "category": "coverage",
        "mutating": true
    },
    {
        "name": "stk_coverage_add_asset",
        "operation": "coverage_add_asset",
        "description": "Assign an object as a coverage asset.",
        "parameters": {
            "type": "object",
            "properties": {
                "coverage_name": {
                    "type": "string",
                    "description": "Coverage definition name"
                },
                "object_name": {
                    "type": "string",
                    "description": "Asset object name"
                }
            },
            "additionalProperties": false,
            "required": [
                "coverage_name",
                "object_name"
            ]
        },
        "category": "coverage",
        "mutating": true
    },
    {
        "name": "stk_coverage_remove_asset",
        "operation": "coverage_remove_asset",
        "description": "Remove an asset from a coverage definition.",
        "parameters": {
            "type": "object",
            "properties": {
                "coverage_name": {
                    "type": "string",
                    "description": "Coverage definition name"
                },
                "object_name": {
                    "type": "string",
                    "description": "Asset object name"
                }
            },
            "additionalProperties": false,
            "required": [
                "coverage_name",
                "object_name"
            ]
        },
        "category": "coverage",
        "mutating": true
    },
    {
        "name": "stk_coverage_compute",
        "operation": "coverage_compute",
        "description": "Compute coverage accesses and return high-level coverage statistics.",
        "parameters": {
            "type": "object",
            "properties": {
                "coverage_name": {
                    "type": "string",
                    "description": "Coverage definition name"
                }
            },
            "additionalProperties": false,
            "required": [
                "coverage_name"
            ]
        },
        "category": "coverage",
        "mutating": true
    },
    {
        "name": "stk_coverage_stats",
        "operation": "coverage_stats",
        "description": "Read coverage statistics without recomputing accesses.",
        "parameters": {
            "type": "object",
            "properties": {
                "coverage_name": {
                    "type": "string",
                    "description": "Coverage definition name"
                },
                "provider": {
                    "type": "string",
                    "description": "Coverage data provider",
                    "default": "Percent Coverage"
                },
                "max_rows": {
                    "type": "integer",
                    "description": "Maximum rows",
                    "default": 200
                }
            },
            "additionalProperties": false,
            "required": [
                "coverage_name"
            ]
        },
        "category": "coverage",
        "mutating": false
    },
    {
        "name": "stk_coverage_fom_create",
        "operation": "coverage_fom_create",
        "description": "Create a Figure of Merit under a coverage definition and optionally set its type.",
        "parameters": {
            "type": "object",
            "properties": {
                "coverage_name": {
                    "type": "string",
                    "description": "Coverage definition name"
                },
                "name": {
                    "type": "string",
                    "description": "Figure-of-merit name",
                    "default": "FOM1"
                },
                "definition_type": {
                    "type": "integer",
                    "description": "STK FOM definition type index (0 = default Coverage)",
                    "default": 0
                }
            },
            "additionalProperties": false,
            "required": [
                "coverage_name"
            ]
        },
        "category": "coverage",
        "mutating": true
    },
    {
        "name": "stk_coverage_fom_query",
        "operation": "coverage_fom_query",
        "description": "Query a figure-of-merit data provider.",
        "parameters": {
            "type": "object",
            "properties": {
                "coverage_name": {
                    "type": "string",
                    "description": "Coverage definition name"
                },
                "fom_name": {
                    "type": "string",
                    "description": "FOM name"
                },
                "provider": {
                    "type": "string",
                    "description": "FOM data provider",
                    "default": "FOM Value"
                },
                "max_rows": {
                    "type": "integer",
                    "description": "Maximum rows",
                    "default": 200
                }
            },
            "additionalProperties": false,
            "required": [
                "coverage_name",
                "fom_name"
            ]
        },
        "category": "coverage",
        "mutating": false
    },
    {
        "name": "stk_coverage_grid_inspector",
        "operation": "coverage_grid_inspector",
        "description": "Select a grid point and read its point/region coverage values.",
        "parameters": {
            "type": "object",
            "properties": {
                "coverage_name": {
                    "type": "string",
                    "description": "Coverage definition name"
                },
                "latitude_deg": {
                    "type": "number",
                    "description": "Grid point latitude",
                    "minimum": -90,
                    "maximum": 90
                },
                "longitude_deg": {
                    "type": "number",
                    "description": "Grid point longitude",
                    "minimum": -180,
                    "maximum": 180
                }
            },
            "additionalProperties": false,
            "required": [
                "coverage_name",
                "latitude_deg",
                "longitude_deg"
            ]
        },
        "category": "coverage",
        "mutating": true
    },
    {
        "name": "stk_data_provider_list",
        "operation": "data_provider_list",
        "description": "List data providers and their groups for an object.",
        "parameters": {
            "type": "object",
            "properties": {
                "object_name": {
                    "type": "string",
                    "description": "Object name"
                }
            },
            "additionalProperties": false,
            "required": [
                "object_name"
            ]
        },
        "category": "data",
        "mutating": false
    },
    {
        "name": "stk_data_provider_query",
        "operation": "data_provider_query",
        "description": "Execute a data-provider query and return a table of results. Use a single time for an instant query or start/stop/step for a time series.",
        "parameters": {
            "type": "object",
            "properties": {
                "object_name": {
                    "type": "string",
                    "description": "Object name"
                },
                "provider": {
                    "type": "string",
                    "description": "Data provider name, e.g. Cartesian Position"
                },
                "group": {
                    "type": "string",
                    "description": "Group name, e.g. ICRF"
                },
                "time": {
                    "type": "string",
                    "description": "Single query time"
                },
                "start_time": {
                    "type": "string",
                    "description": "Series start time"
                },
                "stop_time": {
                    "type": "string",
                    "description": "Series stop time"
                },
                "step_sec": {
                    "type": "number",
                    "description": "Series step (seconds)",
                    "default": 60
                },
                "max_rows": {
                    "type": "integer",
                    "description": "Maximum rows",
                    "default": 2000
                }
            },
            "additionalProperties": false,
            "required": [
                "object_name",
                "provider"
            ]
        },
        "category": "data",
        "mutating": false
    },
    {
        "name": "stk_report_create",
        "operation": "report_create",
        "description": "Generate an STK report through ReportCreate and return the file path plus preview.",
        "parameters": {
            "type": "object",
            "properties": {
                "object_name": {
                    "type": "string",
                    "description": "Object name"
                },
                "style": {
                    "type": "string",
                    "description": "STK report style, e.g. 'Access' or 'LLA Position'"
                },
                "file_path": {
                    "type": "string",
                    "description": "Output path (defaults under ~/.spaceone-stk-mcp/reports)"
                },
                "access_object": {
                    "type": "string",
                    "description": "Optional access target object name"
                },
                "start_time": {
                    "type": "string",
                    "description": "Report start time"
                },
                "stop_time": {
                    "type": "string",
                    "description": "Report stop time"
                },
                "step_sec": {
                    "type": "number",
                    "description": "Report time step"
                },
                "additional_data": {
                    "type": "string",
                    "description": "STK ReportCreate AdditionalData value"
                },
                "summary": {
                    "type": "string",
                    "description": "Summary option: Include or Only"
                }
            },
            "additionalProperties": false,
            "required": [
                "object_name",
                "style"
            ]
        },
        "category": "report",
        "mutating": true
    },
    {
        "name": "stk_object_list",
        "operation": "object_list",
        "description": "List objects in the scenario, optionally filtered by class and including nested children such as sensors and equipment.",
        "parameters": {
            "type": "object",
            "properties": {
                "class_name": {
                    "type": "string",
                    "description": "Filter by ClassName, e.g. Satellite, Facility, Sensor, CoverageDefinition"
                },
                "include_children": {
                    "type": "boolean",
                    "description": "Recurse into child objects",
                    "default": true
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum recursion depth",
                    "default": 3,
                    "minimum": 0,
                    "maximum": 8
                }
            },
            "additionalProperties": false
        },
        "category": "objects",
        "mutating": false
    },
    {
        "name": "stk_equipment_create",
        "operation": "equipment_create",
        "description": "Create an antenna, receiver, transmitter or radar on a parent object.",
        "parameters": {
            "type": "object",
            "properties": {
                "parent_name": {
                    "type": "string",
                    "description": "Parent satellite/facility/aircraft name"
                },
                "name": {
                    "type": "string",
                    "description": "Equipment name"
                },
                "equipment_type": {
                    "type": "string",
                    "description": "Equipment class",
                    "enum": [
                        "Antenna",
                        "Receiver",
                        "Transmitter",
                        "Radar"
                    ],
                    "default": "Transmitter"
                },
                "model": {
                    "type": "string",
                    "description": "Optional STK model name, e.g. 'Simple Transmitter Model'"
                },
                "replace_existing": {
                    "type": "boolean",
                    "description": "Unload an existing equipment with this name",
                    "default": false
                }
            },
            "additionalProperties": false,
            "required": [
                "parent_name",
                "name"
            ]
        },
        "category": "equipment",
        "mutating": true
    },
    {
        "name": "stk_equipment_configure",
        "operation": "equipment_configure",
        "description": "Configure a transmitter (frequency/EIRP/data rate), antenna (design frequency/diameter) or receiver (G/T). Only writable model properties are applied; unsupported fields are returned in errors.",
        "parameters": {
            "type": "object",
            "properties": {
                "parent_name": {
                    "type": "string",
                    "description": "Parent object name"
                },
                "name": {
                    "type": "string",
                    "description": "Equipment name"
                },
                "model": {
                    "type": "string",
                    "description": "Optional STK model name"
                },
                "frequency_mhz": {
                    "type": "number",
                    "description": "Transmitter/antenna frequency (MHz)"
                },
                "bandwidth_hz": {
                    "type": "number",
                    "description": "Receiver bandwidth (Hz)"
                },
                "g_over_t_db_k": {
                    "type": "number",
                    "description": "Receiver G/T (dB/K)"
                },
                "eirp_dbw": {
                    "type": "number",
                    "description": "Transmitter EIRP (dBW)"
                },
                "data_rate_bps": {
                    "type": "number",
                    "description": "Transmitter data rate (bps)"
                },
                "diameter_m": {
                    "type": "number",
                    "description": "Antenna diameter (m)"
                },
                "efficiency": {
                    "type": "number",
                    "description": "Antenna efficiency (0-1)",
                    "minimum": 0,
                    "maximum": 1
                }
            },
            "additionalProperties": false,
            "required": [
                "parent_name",
                "name"
            ]
        },
        "category": "equipment",
        "mutating": true
    },
    {
        "name": "stk_equipment_list",
        "operation": "equipment_list",
        "description": "List antennas, receivers, transmitters and radars on a parent object.",
        "parameters": {
            "type": "object",
            "properties": {
                "parent_name": {
                    "type": "string",
                    "description": "Parent object name"
                }
            },
            "additionalProperties": false,
            "required": [
                "parent_name"
            ]
        },
        "category": "equipment",
        "mutating": false
    },
    {
        "name": "stk_platform_create",
        "operation": "platform_create",
        "description": "Create an aircraft, ship or ground vehicle.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Platform name"
                },
                "platform_type": {
                    "type": "string",
                    "description": "Platform class",
                    "enum": [
                        "Aircraft",
                        "Ship",
                        "GroundVehicle"
                    ]
                },
                "replace_existing": {
                    "type": "boolean",
                    "description": "Unload an existing platform",
                    "default": false
                }
            },
            "additionalProperties": false,
            "required": [
                "name",
                "platform_type"
            ]
        },
        "category": "platform",
        "mutating": true
    },
    {
        "name": "stk_platform_set_waypoints",
        "operation": "platform_set_waypoints",
        "description": "Set a time-specified great-arc route for an aircraft, ship or ground vehicle and propagate it.",
        "parameters": {
            "type": "object",
            "properties": {
                "platform_name": {
                    "type": "string",
                    "description": "Platform name"
                },
                "waypoints": {
                    "type": "array",
                    "description": "Waypoints in time order",
                    "items": {
                        "type": "object",
                        "additionalProperties": false,
                        "properties": {
                            "time": {
                                "type": "string",
                                "description": "Waypoint time (UTCG/ISO)"
                            },
                            "latitude_deg": {
                                "type": "number",
                                "description": "Latitude (-90..90)"
                            },
                            "longitude_deg": {
                                "type": "number",
                                "description": "Longitude (-180..180)"
                            },
                            "altitude_km": {
                                "type": "number",
                                "description": "Altitude (km)"
                            },
                            "turn_radius_km": {
                                "type": "number",
                                "description": "Turn radius (km)"
                            }
                        },
                        "required": [
                            "time",
                            "latitude_deg",
                            "longitude_deg"
                        ]
                    }
                }
            },
            "additionalProperties": false,
            "required": [
                "platform_name",
                "waypoints"
            ]
        },
        "category": "platform",
        "mutating": true
    },
    {
        "name": "stk_area_target_create",
        "operation": "area_target_create",
        "description": "Create a ground area target, optionally as an ellipse.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Area target name"
                },
                "center_lat": {
                    "type": "number",
                    "description": "Ellipse center latitude",
                    "minimum": -90,
                    "maximum": 90
                },
                "center_lon": {
                    "type": "number",
                    "description": "Ellipse center longitude",
                    "minimum": -180,
                    "maximum": 180
                },
                "semi_major_axis_km": {
                    "type": "number",
                    "description": "Ellipse semi-major axis (km)"
                },
                "semi_minor_axis_km": {
                    "type": "number",
                    "description": "Ellipse semi-minor axis (km)"
                },
                "bearing_deg": {
                    "type": "number",
                    "description": "Ellipse bearing (deg)",
                    "default": 0.0
                },
                "replace_existing": {
                    "type": "boolean",
                    "description": "Unload an existing area target",
                    "default": false
                }
            },
            "additionalProperties": false,
            "required": [
                "name"
            ]
        },
        "category": "objects",
        "mutating": true
    },
    {
        "name": "stk_area_target_set_polygon",
        "operation": "area_target_set_polygon",
        "description": "Configure an existing area target as a polygon boundary from lat/lon points.",
        "parameters": {
            "type": "object",
            "properties": {
                "area_target_name": {
                    "type": "string",
                    "description": "Area target name"
                },
                "points": {
                    "type": "array",
                    "description": "Boundary points in order",
                    "items": {
                        "type": "object",
                        "additionalProperties": false,
                        "properties": {
                            "latitude_deg": {
                                "type": "number",
                                "description": "Latitude (-90..90)"
                            },
                            "longitude_deg": {
                                "type": "number",
                                "description": "Longitude (-180..180)"
                            }
                        },
                        "required": [
                            "latitude_deg",
                            "longitude_deg"
                        ]
                    }
                },
                "clear_existing": {
                    "type": "boolean",
                    "description": "Remove existing boundary points first",
                    "default": true
                }
            },
            "additionalProperties": false,
            "required": [
                "area_target_name",
                "points"
            ]
        },
        "category": "objects",
        "mutating": true
    },
    {
        "name": "stk_chain_create",
        "operation": "chain_create",
        "description": "Create an access chain and optionally add objects to it.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Chain name"
                },
                "objects": {
                    "type": "array",
                    "description": "Object names/paths",
                    "default": [],
                    "items": {
                        "type": "string"
                    }
                },
                "replace_existing": {
                    "type": "boolean",
                    "description": "Unload an existing chain",
                    "default": false
                }
            },
            "additionalProperties": false,
            "required": [
                "name"
            ]
        },
        "category": "chain",
        "mutating": true
    },
    {
        "name": "stk_chain_compute_access",
        "operation": "chain_compute_access",
        "description": "Compute access through a chain and return the computed strand intervals.",
        "parameters": {
            "type": "object",
            "properties": {
                "chain_name": {
                    "type": "string",
                    "description": "Chain name"
                }
            },
            "additionalProperties": false,
            "required": [
                "chain_name"
            ]
        },
        "category": "chain",
        "mutating": true
    },
    {
        "name": "stk_constellation_build_walker",
        "operation": "constellation_build_walker",
        "description": "Batch-build a Walker Delta/Star constellation from circular orbits and add all generated satellites to a constellation object.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Constellation name"
                },
                "total_sats": {
                    "type": "integer",
                    "description": "Total satellites (1-200)",
                    "default": 12,
                    "minimum": 1,
                    "maximum": 200
                },
                "planes": {
                    "type": "integer",
                    "description": "Number of orbital planes",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 200
                },
                "pattern": {
                    "type": "string",
                    "description": "Walker pattern: delta (360° RAAN spread) or star (180°)",
                    "enum": [
                        "walker_delta",
                        "walker_star"
                    ],
                    "default": "walker_delta"
                },
                "altitude_km": {
                    "type": "number",
                    "description": "Circular altitude (km)",
                    "default": 550,
                    "minimum": 0
                },
                "inclination_deg": {
                    "type": "number",
                    "description": "Inclination (deg)",
                    "default": 53,
                    "minimum": 0,
                    "maximum": 180
                },
                "phasing": {
                    "type": "integer",
                    "description": "Walker phasing factor F",
                    "default": 0,
                    "minimum": 0,
                    "maximum": 199
                },
                "raan0_deg": {
                    "type": "number",
                    "description": "RAAN of the first plane (deg)",
                    "default": 0
                },
                "mean_anomaly0_deg": {
                    "type": "number",
                    "description": "Mean anomaly of the first satellite (deg)",
                    "default": 0
                },
                "epoch": {
                    "type": "string",
                    "description": "Optional orbit epoch"
                },
                "propagator": {
                    "type": "string",
                    "description": "Propagator",
                    "enum": [
                        "TwoBody",
                        "J2Perturbation",
                        "J4Perturbation",
                        "HPOP"
                    ],
                    "default": "TwoBody"
                },
                "name_prefix": {
                    "type": "string",
                    "description": "Satellite name prefix",
                    "default": "Sat"
                },
                "replace_existing": {
                    "type": "boolean",
                    "description": "Unload an existing constellation with this name",
                    "default": false
                }
            },
            "additionalProperties": false,
            "required": [
                "name",
                "total_sats",
                "planes"
            ]
        },
        "category": "constellation",
        "mutating": true
    },
    {
        "name": "stk_astrogator_summary",
        "operation": "astrogator_summary",
        "description": "List the Astrogator main-sequence segments for a satellite.",
        "parameters": {
            "type": "object",
            "properties": {
                "satellite_name": {
                    "type": "string",
                    "description": "Satellite name"
                }
            },
            "additionalProperties": false,
            "required": [
                "satellite_name"
            ]
        },
        "category": "astrogator",
        "mutating": false
    },
    {
        "name": "stk_astrogator_run",
        "operation": "astrogator_run",
        "description": "Run the Astrogator main sequence (RunMCS) and return the resulting state.",
        "parameters": {
            "type": "object",
            "properties": {
                "satellite_name": {
                    "type": "string",
                    "description": "Satellite name"
                }
            },
            "additionalProperties": false,
            "required": [
                "satellite_name"
            ]
        },
        "category": "astrogator",
        "mutating": true
    },
    {
        "name": "stk_report_list_styles",
        "operation": "report_list_styles",
        "description": "List available STK report styles (*.rst) from the installed STKData and the user's Config\\Styles directories. Use a returned name as report_create.style.",
        "parameters": {
            "type": "object",
            "properties": {
                "include_user": {
                    "type": "boolean",
                    "description": "Include the user's Config\\Styles directory",
                    "default": true
                },
                "category": {
                    "type": "string",
                    "description": "Optional category filter, e.g. Access or Satellite"
                },
                "max_styles": {
                    "type": "integer",
                    "description": "Maximum returned styles",
                    "default": 500
                }
            },
            "additionalProperties": false
        },
        "category": "report",
        "mutating": false
    },
    {
        "name": "stk_execute_command",
        "operation": "stk_execute_command",
        "description": "Execute a raw STK Connect command. transport=com uses the COM ExecuteCommand path; transport=tcp uses the Connect socket and returns raw reply data.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Connect command, e.g. 'GetSTKVersion /'"
                },
                "transport": {
                    "type": "string",
                    "description": "Execution channel",
                    "enum": [
                        "com",
                        "tcp",
                        "auto"
                    ],
                    "default": "com"
                }
            },
            "additionalProperties": false,
            "required": [
                "command"
            ]
        },
        "category": "connection",
        "mutating": true
    },
    {
        "name": "stk_selftest",
        "operation": "stk_selftest",
        "description": "Run an end-to-end STK smoke test: scenario, satellite orbit, propagation, state query, facility, access, coverage and report. With an existing scenario open it performs read-only checks unless replace_scenario=true.",
        "parameters": {
            "type": "object",
            "properties": {
                "replace_scenario": {
                    "type": "boolean",
                    "description": "Close the current scenario and run the full write test",
                    "default": false
                }
            },
            "additionalProperties": false
        },
        "category": "connection",
        "mutating": true
    }
];
export const ALL_TOOLS = [
    {
        "name": "stk_access_compute",
        "operation": "access_compute",
        "description": "Compute access intervals between two objects over the scenario interval.",
        "parameters": {
            "type": "object",
            "properties": {
                "from_object": {
                    "type": "string",
                    "description": "Source object name"
                },
                "to_object": {
                    "type": "string",
                    "description": "Target object name"
                },
                "time_step_sec": {
                    "type": "number",
                    "description": "Access computation time step (seconds)"
                }
            },
            "additionalProperties": false,
            "required": [
                "from_object",
                "to_object"
            ]
        },
        "category": "access",
        "mutating": true
    },
    {
        "name": "stk_access_batch",
        "operation": "access_batch",
        "description": "Compute access from one source object to several target objects.",
        "parameters": {
            "type": "object",
            "properties": {
                "from_object": {
                    "type": "string",
                    "description": "Source object name"
                },
                "to_objects": {
                    "type": "array",
                    "description": "Target names",
                    "items": {
                        "type": "string"
                    }
                },
                "time_step_sec": {
                    "type": "number",
                    "description": "Access computation time step (seconds)"
                }
            },
            "additionalProperties": false,
            "required": [
                "from_object",
                "to_objects"
            ]
        },
        "category": "access",
        "mutating": true
    },
    {
        "name": "stk_access_report",
        "operation": "access_report",
        "description": "Generate an STK access report (Access style) between two objects.",
        "parameters": {
            "type": "object",
            "properties": {
                "from_object": {
                    "type": "string",
                    "description": "Source object name"
                },
                "to_object": {
                    "type": "string",
                    "description": "Target object name"
                },
                "file_path": {
                    "type": "string",
                    "description": "Optional report output path"
                }
            },
            "additionalProperties": false,
            "required": [
                "from_object",
                "to_object"
            ]
        },
        "category": "access",
        "mutating": true
    },
    {
        "name": "stk_access_set_constraint",
        "operation": "access_set_constraint",
        "description": "Set a minimum/maximum access constraint (for example ElevationAngle) on an object.",
        "parameters": {
            "type": "object",
            "properties": {
                "object_name": {
                    "type": "string",
                    "description": "Object to constrain"
                },
                "constraint": {
                    "type": "string",
                    "description": "Constraint name",
                    "enum": [
                        "ElevationAngle",
                        "AzimuthAngle",
                        "Range",
                        "Duration",
                        "BetaAngle",
                        "Altitude",
                        "Lighting",
                        "LineOfSight",
                        "GroundElevationAngle",
                        "SunElevationAngle"
                    ],
                    "default": "ElevationAngle"
                },
                "minimum": {
                    "type": "number",
                    "description": "Minimum value"
                },
                "maximum": {
                    "type": "number",
                    "description": "Maximum value"
                }
            },
            "additionalProperties": false,
            "required": [
                "object_name"
            ]
        },
        "category": "access",
        "mutating": true
    },
    {
        "name": "stk_access_clear_constraints",
        "operation": "access_clear_constraints",
        "description": "Remove all access constraints from an object.",
        "parameters": {
            "type": "object",
            "properties": {
                "object_name": {
                    "type": "string",
                    "description": "Object name"
                }
            },
            "additionalProperties": false,
            "required": [
                "object_name"
            ]
        },
        "category": "access",
        "mutating": true
    },
    {
        "name": "stk_data_provider_list",
        "operation": "data_provider_list",
        "description": "List data providers and their groups for an object.",
        "parameters": {
            "type": "object",
            "properties": {
                "object_name": {
                    "type": "string",
                    "description": "Object name"
                }
            },
            "additionalProperties": false,
            "required": [
                "object_name"
            ]
        },
        "category": "data",
        "mutating": false
    },
    {
        "name": "stk_data_provider_query",
        "operation": "data_provider_query",
        "description": "Execute a data-provider query and return a table of results. Use a single time for an instant query or start/stop/step for a time series.",
        "parameters": {
            "type": "object",
            "properties": {
                "object_name": {
                    "type": "string",
                    "description": "Object name"
                },
                "provider": {
                    "type": "string",
                    "description": "Data provider name, e.g. Cartesian Position"
                },
                "group": {
                    "type": "string",
                    "description": "Group name, e.g. ICRF"
                },
                "time": {
                    "type": "string",
                    "description": "Single query time"
                },
                "start_time": {
                    "type": "string",
                    "description": "Series start time"
                },
                "stop_time": {
                    "type": "string",
                    "description": "Series stop time"
                },
                "step_sec": {
                    "type": "number",
                    "description": "Series step (seconds)",
                    "default": 60
                },
                "max_rows": {
                    "type": "integer",
                    "description": "Maximum rows",
                    "default": 2000
                }
            },
            "additionalProperties": false,
            "required": [
                "object_name",
                "provider"
            ]
        },
        "category": "data",
        "mutating": false
    },
    {
        "name": "stk_lighting_compute",
        "operation": "lighting_compute",
        "description": "Compute sunlight/eclipse intervals for an object.",
        "parameters": {
            "type": "object",
            "properties": {
                "object_name": {
                    "type": "string",
                    "description": "Object name"
                },
                "group": {
                    "type": "string",
                    "description": "Lighting group",
                    "default": "Sunlight"
                }
            },
            "additionalProperties": false,
            "required": [
                "object_name"
            ]
        },
        "category": "analysis",
        "mutating": true
    },
    {
        "name": "stk_report_list_styles",
        "operation": "report_list_styles",
        "description": "List available STK report styles (*.rst) from the installed STKData and the user's Config\\Styles directories. Use a returned name as report_create.style.",
        "parameters": {
            "type": "object",
            "properties": {
                "include_user": {
                    "type": "boolean",
                    "description": "Include the user's Config\\Styles directory",
                    "default": true
                },
                "category": {
                    "type": "string",
                    "description": "Optional category filter, e.g. Access or Satellite"
                },
                "max_styles": {
                    "type": "integer",
                    "description": "Maximum returned styles",
                    "default": 500
                }
            },
            "additionalProperties": false
        },
        "category": "report",
        "mutating": false
    },
    {
        "name": "stk_report_create",
        "operation": "report_create",
        "description": "Generate an STK report through ReportCreate and return the file path plus preview.",
        "parameters": {
            "type": "object",
            "properties": {
                "object_name": {
                    "type": "string",
                    "description": "Object name"
                },
                "style": {
                    "type": "string",
                    "description": "STK report style, e.g. 'Access' or 'LLA Position'"
                },
                "file_path": {
                    "type": "string",
                    "description": "Output path (defaults under ~/.spaceone-stk-mcp/reports)"
                },
                "access_object": {
                    "type": "string",
                    "description": "Optional access target object name"
                },
                "start_time": {
                    "type": "string",
                    "description": "Report start time"
                },
                "stop_time": {
                    "type": "string",
                    "description": "Report stop time"
                },
                "step_sec": {
                    "type": "number",
                    "description": "Report time step"
                },
                "additional_data": {
                    "type": "string",
                    "description": "STK ReportCreate AdditionalData value"
                },
                "summary": {
                    "type": "string",
                    "description": "Summary option: Include or Only"
                }
            },
            "additionalProperties": false,
            "required": [
                "object_name",
                "style"
            ]
        },
        "category": "report",
        "mutating": true
    },
    {
        "name": "stk_animation_control",
        "operation": "animation_control",
        "description": "Control scenario animation: play, pause, stop, step, set_time or set_rate.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Animation action",
                    "enum": [
                        "play",
                        "pause",
                        "stop",
                        "step_forward",
                        "step_backward",
                        "set_time",
                        "set_rate"
                    ]
                },
                "direction": {
                    "type": "string",
                    "description": "Play direction",
                    "enum": [
                        "forward",
                        "backward"
                    ],
                    "default": "forward"
                },
                "epoch_seconds": {
                    "type": "number",
                    "description": "Seconds from scenario start for set_time"
                },
                "time": {
                    "type": "string",
                    "description": "Absolute time for set_time"
                },
                "high_speed": {
                    "type": "number",
                    "description": "Playback multiplier for set_rate"
                }
            },
            "additionalProperties": false,
            "required": [
                "action"
            ]
        },
        "category": "animation",
        "mutating": true
    },
    {
        "name": "stk_animation_info",
        "operation": "animation_info",
        "description": "Read the current animation time, scenario time bounds and playback rate.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": false
        },
        "category": "animation",
        "mutating": false
    },
    {
        "name": "stk_scenario_set_view",
        "operation": "scenario_set_view",
        "description": "Activate the 2D/3D graphics windows and optionally show all objects.",
        "parameters": {
            "type": "object",
            "properties": {
                "show_3d": {
                    "type": "boolean",
                    "description": "Activate the 3D window",
                    "default": true
                },
                "show_2d": {
                    "type": "boolean",
                    "description": "Activate the 2D window",
                    "default": false
                },
                "maximize": {
                    "type": "boolean",
                    "description": "Maximize the activated window",
                    "default": false
                }
            },
            "additionalProperties": false
        },
        "category": "animation",
        "mutating": true
    },
    {
        "name": "stk_connect",
        "operation": "stk_connect",
        "description": "Launch or attach to STK 11/12 through COM. Existing instances are reused; a new instance is started only when no STK automation object is running.",
        "parameters": {
            "type": "object",
            "properties": {
                "prog_id": {
                    "type": "string",
                    "description": "STK ProgID. Omit to use auto-detection (STK 11 preferred, then STK 12).",
                    "enum": [
                        "STK11.Application",
                        "STK12.Application"
                    ]
                },
                "visible": {
                    "type": "boolean",
                    "description": "Show the STK desktop window (headed mode)",
                    "default": true
                },
                "user_control": {
                    "type": "boolean",
                    "description": "Allow the user to interact with STK",
                    "default": true
                },
                "force": {
                    "type": "boolean",
                    "description": "Reconnect even if a session is already active",
                    "default": false
                }
            },
            "additionalProperties": false
        },
        "category": "connection",
        "mutating": true
    },
    {
        "name": "stk_disconnect",
        "operation": "stk_disconnect",
        "description": "Release the STK COM reference. Do NOT call this at the end of a modeling or analysis task: leave the scenario open for the user. The STK process is not quit and the scenario is not closed by default.",
        "parameters": {
            "type": "object",
            "properties": {
                "quit": {
                    "type": "boolean",
                    "description": "Quit the STK application",
                    "default": false
                },
                "close_scenario": {
                    "type": "boolean",
                    "description": "Close the current scenario first",
                    "default": false
                }
            },
            "additionalProperties": false
        },
        "category": "connection",
        "mutating": true
    },
    {
        "name": "stk_status",
        "operation": "stk_status",
        "description": "Report whether the kernel is connected, the STK version/PID and the open scenario.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": false
        },
        "category": "connection",
        "mutating": false
    },
    {
        "name": "stk_capabilities",
        "operation": "stk_capabilities",
        "description": "List the STK version, object types supported by the installed license, and the available Connect port. Useful before building a workflow.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": false
        },
        "category": "connection",
        "mutating": false
    },
    {
        "name": "stk_execute_command",
        "operation": "stk_execute_command",
        "description": "Execute a raw STK Connect command. transport=com uses the COM ExecuteCommand path; transport=tcp uses the Connect socket and returns raw reply data.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Connect command, e.g. 'GetSTKVersion /'"
                },
                "transport": {
                    "type": "string",
                    "description": "Execution channel",
                    "enum": [
                        "com",
                        "tcp",
                        "auto"
                    ],
                    "default": "com"
                }
            },
            "additionalProperties": false,
            "required": [
                "command"
            ]
        },
        "category": "connection",
        "mutating": true
    },
    {
        "name": "stk_selftest",
        "operation": "stk_selftest",
        "description": "Run an end-to-end STK smoke test: scenario, satellite orbit, propagation, state query, facility, access, coverage and report. With an existing scenario open it performs read-only checks unless replace_scenario=true.",
        "parameters": {
            "type": "object",
            "properties": {
                "replace_scenario": {
                    "type": "boolean",
                    "description": "Close the current scenario and run the full write test",
                    "default": false
                }
            },
            "additionalProperties": false
        },
        "category": "connection",
        "mutating": true
    },
    {
        "name": "stk_coverage_create",
        "operation": "coverage_create",
        "description": "Create a coverage definition.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Coverage definition name"
                },
                "replace_existing": {
                    "type": "boolean",
                    "description": "Unload an existing coverage definition",
                    "default": false
                }
            },
            "additionalProperties": false,
            "required": [
                "name"
            ]
        },
        "category": "coverage",
        "mutating": true
    },
    {
        "name": "stk_coverage_set_grid",
        "operation": "coverage_set_grid",
        "description": "Set a global or latitude/longitude coverage grid.",
        "parameters": {
            "type": "object",
            "properties": {
                "coverage_name": {
                    "type": "string",
                    "description": "Coverage definition name"
                },
                "mode": {
                    "type": "string",
                    "description": "Grid bounds",
                    "enum": [
                        "global",
                        "lat_lon_region",
                        "lat_band"
                    ],
                    "default": "global"
                },
                "min_lat": {
                    "type": "number",
                    "description": "Region minimum latitude",
                    "minimum": -90,
                    "maximum": 90
                },
                "max_lat": {
                    "type": "number",
                    "description": "Region maximum latitude",
                    "minimum": -90,
                    "maximum": 90
                },
                "min_lon": {
                    "type": "number",
                    "description": "Region minimum longitude",
                    "minimum": -180,
                    "maximum": 180
                },
                "max_lon": {
                    "type": "number",
                    "description": "Region maximum longitude",
                    "minimum": -180,
                    "maximum": 180
                },
                "lat_resolution_deg": {
                    "type": "number",
                    "description": "Latitude resolution (deg)",
                    "default": 5.0
                },
                "lon_resolution_deg": {
                    "type": "number",
                    "description": "Longitude resolution (deg)",
                    "default": 5.0
                }
            },
            "additionalProperties": false,
            "required": [
                "coverage_name"
            ]
        },
        "category": "coverage",
        "mutating": true
    },
    {
        "name": "stk_coverage_add_asset",
        "operation": "coverage_add_asset",
        "description": "Assign an object as a coverage asset.",
        "parameters": {
            "type": "object",
            "properties": {
                "coverage_name": {
                    "type": "string",
                    "description": "Coverage definition name"
                },
                "object_name": {
                    "type": "string",
                    "description": "Asset object name"
                }
            },
            "additionalProperties": false,
            "required": [
                "coverage_name",
                "object_name"
            ]
        },
        "category": "coverage",
        "mutating": true
    },
    {
        "name": "stk_coverage_remove_asset",
        "operation": "coverage_remove_asset",
        "description": "Remove an asset from a coverage definition.",
        "parameters": {
            "type": "object",
            "properties": {
                "coverage_name": {
                    "type": "string",
                    "description": "Coverage definition name"
                },
                "object_name": {
                    "type": "string",
                    "description": "Asset object name"
                }
            },
            "additionalProperties": false,
            "required": [
                "coverage_name",
                "object_name"
            ]
        },
        "category": "coverage",
        "mutating": true
    },
    {
        "name": "stk_coverage_compute",
        "operation": "coverage_compute",
        "description": "Compute coverage accesses and return high-level coverage statistics.",
        "parameters": {
            "type": "object",
            "properties": {
                "coverage_name": {
                    "type": "string",
                    "description": "Coverage definition name"
                }
            },
            "additionalProperties": false,
            "required": [
                "coverage_name"
            ]
        },
        "category": "coverage",
        "mutating": true
    },
    {
        "name": "stk_coverage_stats",
        "operation": "coverage_stats",
        "description": "Read coverage statistics without recomputing accesses.",
        "parameters": {
            "type": "object",
            "properties": {
                "coverage_name": {
                    "type": "string",
                    "description": "Coverage definition name"
                },
                "provider": {
                    "type": "string",
                    "description": "Coverage data provider",
                    "default": "Percent Coverage"
                },
                "max_rows": {
                    "type": "integer",
                    "description": "Maximum rows",
                    "default": 200
                }
            },
            "additionalProperties": false,
            "required": [
                "coverage_name"
            ]
        },
        "category": "coverage",
        "mutating": false
    },
    {
        "name": "stk_coverage_fom_create",
        "operation": "coverage_fom_create",
        "description": "Create a Figure of Merit under a coverage definition and optionally set its type.",
        "parameters": {
            "type": "object",
            "properties": {
                "coverage_name": {
                    "type": "string",
                    "description": "Coverage definition name"
                },
                "name": {
                    "type": "string",
                    "description": "Figure-of-merit name",
                    "default": "FOM1"
                },
                "definition_type": {
                    "type": "integer",
                    "description": "STK FOM definition type index (0 = default Coverage)",
                    "default": 0
                }
            },
            "additionalProperties": false,
            "required": [
                "coverage_name"
            ]
        },
        "category": "coverage",
        "mutating": true
    },
    {
        "name": "stk_coverage_fom_query",
        "operation": "coverage_fom_query",
        "description": "Query a figure-of-merit data provider.",
        "parameters": {
            "type": "object",
            "properties": {
                "coverage_name": {
                    "type": "string",
                    "description": "Coverage definition name"
                },
                "fom_name": {
                    "type": "string",
                    "description": "FOM name"
                },
                "provider": {
                    "type": "string",
                    "description": "FOM data provider",
                    "default": "FOM Value"
                },
                "max_rows": {
                    "type": "integer",
                    "description": "Maximum rows",
                    "default": 200
                }
            },
            "additionalProperties": false,
            "required": [
                "coverage_name",
                "fom_name"
            ]
        },
        "category": "coverage",
        "mutating": false
    },
    {
        "name": "stk_coverage_grid_inspector",
        "operation": "coverage_grid_inspector",
        "description": "Select a grid point and read its point/region coverage values.",
        "parameters": {
            "type": "object",
            "properties": {
                "coverage_name": {
                    "type": "string",
                    "description": "Coverage definition name"
                },
                "latitude_deg": {
                    "type": "number",
                    "description": "Grid point latitude",
                    "minimum": -90,
                    "maximum": 90
                },
                "longitude_deg": {
                    "type": "number",
                    "description": "Grid point longitude",
                    "minimum": -180,
                    "maximum": 180
                }
            },
            "additionalProperties": false,
            "required": [
                "coverage_name",
                "latitude_deg",
                "longitude_deg"
            ]
        },
        "category": "coverage",
        "mutating": true
    },
    {
        "name": "stk_equipment_create",
        "operation": "equipment_create",
        "description": "Create an antenna, receiver, transmitter or radar on a parent object.",
        "parameters": {
            "type": "object",
            "properties": {
                "parent_name": {
                    "type": "string",
                    "description": "Parent satellite/facility/aircraft name"
                },
                "name": {
                    "type": "string",
                    "description": "Equipment name"
                },
                "equipment_type": {
                    "type": "string",
                    "description": "Equipment class",
                    "enum": [
                        "Antenna",
                        "Receiver",
                        "Transmitter",
                        "Radar"
                    ],
                    "default": "Transmitter"
                },
                "model": {
                    "type": "string",
                    "description": "Optional STK model name, e.g. 'Simple Transmitter Model'"
                },
                "replace_existing": {
                    "type": "boolean",
                    "description": "Unload an existing equipment with this name",
                    "default": false
                }
            },
            "additionalProperties": false,
            "required": [
                "parent_name",
                "name"
            ]
        },
        "category": "equipment",
        "mutating": true
    },
    {
        "name": "stk_equipment_list",
        "operation": "equipment_list",
        "description": "List antennas, receivers, transmitters and radars on a parent object.",
        "parameters": {
            "type": "object",
            "properties": {
                "parent_name": {
                    "type": "string",
                    "description": "Parent object name"
                }
            },
            "additionalProperties": false,
            "required": [
                "parent_name"
            ]
        },
        "category": "equipment",
        "mutating": false
    },
    {
        "name": "stk_equipment_delete",
        "operation": "equipment_delete",
        "description": "Delete an antenna/receiver/transmitter/radar from its parent.",
        "parameters": {
            "type": "object",
            "properties": {
                "parent_name": {
                    "type": "string",
                    "description": "Parent object name"
                },
                "name": {
                    "type": "string",
                    "description": "Equipment name"
                }
            },
            "additionalProperties": false,
            "required": [
                "parent_name",
                "name"
            ]
        },
        "category": "equipment",
        "mutating": true
    },
    {
        "name": "stk_equipment_configure",
        "operation": "equipment_configure",
        "description": "Configure a transmitter (frequency/EIRP/data rate), antenna (design frequency/diameter) or receiver (G/T). Only writable model properties are applied; unsupported fields are returned in errors.",
        "parameters": {
            "type": "object",
            "properties": {
                "parent_name": {
                    "type": "string",
                    "description": "Parent object name"
                },
                "name": {
                    "type": "string",
                    "description": "Equipment name"
                },
                "model": {
                    "type": "string",
                    "description": "Optional STK model name"
                },
                "frequency_mhz": {
                    "type": "number",
                    "description": "Transmitter/antenna frequency (MHz)"
                },
                "bandwidth_hz": {
                    "type": "number",
                    "description": "Receiver bandwidth (Hz)"
                },
                "g_over_t_db_k": {
                    "type": "number",
                    "description": "Receiver G/T (dB/K)"
                },
                "eirp_dbw": {
                    "type": "number",
                    "description": "Transmitter EIRP (dBW)"
                },
                "data_rate_bps": {
                    "type": "number",
                    "description": "Transmitter data rate (bps)"
                },
                "diameter_m": {
                    "type": "number",
                    "description": "Antenna diameter (m)"
                },
                "efficiency": {
                    "type": "number",
                    "description": "Antenna efficiency (0-1)",
                    "minimum": 0,
                    "maximum": 1
                }
            },
            "additionalProperties": false,
            "required": [
                "parent_name",
                "name"
            ]
        },
        "category": "equipment",
        "mutating": true
    },
    {
        "name": "stk_object_list",
        "operation": "object_list",
        "description": "List objects in the scenario, optionally filtered by class and including nested children such as sensors and equipment.",
        "parameters": {
            "type": "object",
            "properties": {
                "class_name": {
                    "type": "string",
                    "description": "Filter by ClassName, e.g. Satellite, Facility, Sensor, CoverageDefinition"
                },
                "include_children": {
                    "type": "boolean",
                    "description": "Recurse into child objects",
                    "default": true
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum recursion depth",
                    "default": 3,
                    "minimum": 0,
                    "maximum": 8
                }
            },
            "additionalProperties": false
        },
        "category": "objects",
        "mutating": false
    },
    {
        "name": "stk_object_info",
        "operation": "object_info",
        "description": "Return detailed metadata for one object and optionally its children.",
        "parameters": {
            "type": "object",
            "properties": {
                "object_name": {
                    "type": "string",
                    "description": "Object name or path"
                },
                "include_children": {
                    "type": "boolean",
                    "description": "Include direct children",
                    "default": true
                }
            },
            "additionalProperties": false,
            "required": [
                "object_name"
            ]
        },
        "category": "objects",
        "mutating": false
    },
    {
        "name": "stk_object_delete",
        "operation": "object_delete",
        "description": "Unload an object from the scenario.",
        "parameters": {
            "type": "object",
            "properties": {
                "object_name": {
                    "type": "string",
                    "description": "Object name or path"
                }
            },
            "additionalProperties": false,
            "required": [
                "object_name"
            ]
        },
        "category": "objects",
        "mutating": true
    },
    {
        "name": "stk_facility_create",
        "operation": "facility_create",
        "description": "Create a ground facility at a geodetic position.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Facility name"
                },
                "latitude_deg": {
                    "type": "number",
                    "description": "Latitude (-90..90)",
                    "minimum": -90,
                    "maximum": 90
                },
                "longitude_deg": {
                    "type": "number",
                    "description": "Longitude (-180..180)",
                    "minimum": -180,
                    "maximum": 180
                },
                "altitude_km": {
                    "type": "number",
                    "description": "Altitude above the ellipsoid (km)",
                    "default": 0.0
                },
                "replace_existing": {
                    "type": "boolean",
                    "description": "Unload an existing facility with this name",
                    "default": false
                }
            },
            "additionalProperties": false,
            "required": [
                "name",
                "latitude_deg",
                "longitude_deg"
            ]
        },
        "category": "objects",
        "mutating": true
    },
    {
        "name": "stk_facility_set_position",
        "operation": "facility_set_position",
        "description": "Move an existing facility.",
        "parameters": {
            "type": "object",
            "properties": {
                "facility_name": {
                    "type": "string",
                    "description": "Facility name"
                },
                "latitude_deg": {
                    "type": "number",
                    "description": "Latitude (-90..90)",
                    "minimum": -90,
                    "maximum": 90
                },
                "longitude_deg": {
                    "type": "number",
                    "description": "Longitude (-180..180)",
                    "minimum": -180,
                    "maximum": 180
                },
                "altitude_km": {
                    "type": "number",
                    "description": "Altitude (km)",
                    "default": 0.0
                }
            },
            "additionalProperties": false,
            "required": [
                "facility_name",
                "latitude_deg",
                "longitude_deg"
            ]
        },
        "category": "objects",
        "mutating": true
    },
    {
        "name": "stk_place_create",
        "operation": "place_create",
        "description": "Create a point place at a geodetic position.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Place name"
                },
                "latitude_deg": {
                    "type": "number",
                    "description": "Latitude (-90..90)",
                    "minimum": -90,
                    "maximum": 90
                },
                "longitude_deg": {
                    "type": "number",
                    "description": "Longitude (-180..180)",
                    "minimum": -180,
                    "maximum": 180
                },
                "altitude_km": {
                    "type": "number",
                    "description": "Altitude (km)",
                    "default": 0.0
                },
                "replace_existing": {
                    "type": "boolean",
                    "description": "Unload an existing place with this name",
                    "default": false
                }
            },
            "additionalProperties": false,
            "required": [
                "name",
                "latitude_deg",
                "longitude_deg"
            ]
        },
        "category": "objects",
        "mutating": true
    },
    {
        "name": "stk_place_set_position",
        "operation": "place_set_position",
        "description": "Move an existing point place.",
        "parameters": {
            "type": "object",
            "properties": {
                "place_name": {
                    "type": "string",
                    "description": "Place name"
                },
                "latitude_deg": {
                    "type": "number",
                    "description": "Latitude (-90..90)",
                    "minimum": -90,
                    "maximum": 90
                },
                "longitude_deg": {
                    "type": "number",
                    "description": "Longitude (-180..180)",
                    "minimum": -180,
                    "maximum": 180
                },
                "altitude_km": {
                    "type": "number",
                    "description": "Altitude (km)",
                    "default": 0.0
                }
            },
            "additionalProperties": false,
            "required": [
                "place_name",
                "latitude_deg",
                "longitude_deg"
            ]
        },
        "category": "objects",
        "mutating": true
    },
    {
        "name": "stk_area_target_create",
        "operation": "area_target_create",
        "description": "Create a ground area target, optionally as an ellipse.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Area target name"
                },
                "center_lat": {
                    "type": "number",
                    "description": "Ellipse center latitude",
                    "minimum": -90,
                    "maximum": 90
                },
                "center_lon": {
                    "type": "number",
                    "description": "Ellipse center longitude",
                    "minimum": -180,
                    "maximum": 180
                },
                "semi_major_axis_km": {
                    "type": "number",
                    "description": "Ellipse semi-major axis (km)"
                },
                "semi_minor_axis_km": {
                    "type": "number",
                    "description": "Ellipse semi-minor axis (km)"
                },
                "bearing_deg": {
                    "type": "number",
                    "description": "Ellipse bearing (deg)",
                    "default": 0.0
                },
                "replace_existing": {
                    "type": "boolean",
                    "description": "Unload an existing area target",
                    "default": false
                }
            },
            "additionalProperties": false,
            "required": [
                "name"
            ]
        },
        "category": "objects",
        "mutating": true
    },
    {
        "name": "stk_area_target_set_ellipse",
        "operation": "area_target_set_ellipse",
        "description": "Configure an existing area target as an ellipse.",
        "parameters": {
            "type": "object",
            "properties": {
                "area_target_name": {
                    "type": "string",
                    "description": "Area target name"
                },
                "center_lat": {
                    "type": "number",
                    "description": "Center latitude",
                    "minimum": -90,
                    "maximum": 90
                },
                "center_lon": {
                    "type": "number",
                    "description": "Center longitude",
                    "minimum": -180,
                    "maximum": 180
                },
                "semi_major_axis_km": {
                    "type": "number",
                    "description": "Semi-major axis (km)"
                },
                "semi_minor_axis_km": {
                    "type": "number",
                    "description": "Semi-minor axis (km)"
                },
                "bearing_deg": {
                    "type": "number",
                    "description": "Bearing (deg)",
                    "default": 0.0
                }
            },
            "additionalProperties": false,
            "required": [
                "area_target_name",
                "center_lat",
                "center_lon",
                "semi_major_axis_km",
                "semi_minor_axis_km"
            ]
        },
        "category": "objects",
        "mutating": true
    },
    {
        "name": "stk_area_target_set_polygon",
        "operation": "area_target_set_polygon",
        "description": "Configure an existing area target as a polygon boundary from lat/lon points.",
        "parameters": {
            "type": "object",
            "properties": {
                "area_target_name": {
                    "type": "string",
                    "description": "Area target name"
                },
                "points": {
                    "type": "array",
                    "description": "Boundary points in order",
                    "items": {
                        "type": "object",
                        "additionalProperties": false,
                        "properties": {
                            "latitude_deg": {
                                "type": "number",
                                "description": "Latitude (-90..90)"
                            },
                            "longitude_deg": {
                                "type": "number",
                                "description": "Longitude (-180..180)"
                            }
                        },
                        "required": [
                            "latitude_deg",
                            "longitude_deg"
                        ]
                    }
                },
                "clear_existing": {
                    "type": "boolean",
                    "description": "Remove existing boundary points first",
                    "default": true
                }
            },
            "additionalProperties": false,
            "required": [
                "area_target_name",
                "points"
            ]
        },
        "category": "objects",
        "mutating": true
    },
    {
        "name": "stk_area_target_add_boundary_point",
        "operation": "area_target_add_boundary_point",
        "description": "Append one boundary point to an area target (switches it to polygon mode).",
        "parameters": {
            "type": "object",
            "properties": {
                "area_target_name": {
                    "type": "string",
                    "description": "Area target name"
                },
                "latitude_deg": {
                    "type": "number",
                    "description": "Latitude (-90..90)",
                    "minimum": -90,
                    "maximum": 90
                },
                "longitude_deg": {
                    "type": "number",
                    "description": "Longitude (-180..180)",
                    "minimum": -180,
                    "maximum": 180
                }
            },
            "additionalProperties": false,
            "required": [
                "area_target_name",
                "latitude_deg",
                "longitude_deg"
            ]
        },
        "category": "objects",
        "mutating": true
    },
    {
        "name": "stk_target_set_position",
        "operation": "target_set_position",
        "description": "Set a target position from geodetic coordinates or spherical (declination, right ascension, altitude).",
        "parameters": {
            "type": "object",
            "properties": {
                "target_name": {
                    "type": "string",
                    "description": "Target name"
                },
                "mode": {
                    "type": "string",
                    "description": "Position representation",
                    "enum": [
                        "geodetic",
                        "spherical"
                    ],
                    "default": "geodetic"
                },
                "latitude_deg": {
                    "type": "number",
                    "description": "Geodetic latitude (-90..90)",
                    "minimum": -90,
                    "maximum": 90
                },
                "longitude_deg": {
                    "type": "number",
                    "description": "Geodetic longitude (-180..180)",
                    "minimum": -180,
                    "maximum": 180
                },
                "altitude_km": {
                    "type": "number",
                    "description": "Altitude (km)",
                    "default": 0.0
                },
                "declination_deg": {
                    "type": "number",
                    "description": "Spherical declination (-90..90)",
                    "minimum": -90,
                    "maximum": 90
                },
                "right_ascension_deg": {
                    "type": "number",
                    "description": "Spherical right ascension (deg)"
                }
            },
            "additionalProperties": false,
            "required": [
                "target_name"
            ]
        },
        "category": "objects",
        "mutating": true
    },
    {
        "name": "stk_target_create",
        "operation": "target_create",
        "description": "Create a celestial target object (star-like pointing target).",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Target name"
                },
                "replace_existing": {
                    "type": "boolean",
                    "description": "Unload an existing target",
                    "default": false
                }
            },
            "additionalProperties": false,
            "required": [
                "name"
            ]
        },
        "category": "objects",
        "mutating": true
    },
    {
        "name": "stk_sensor_create",
        "operation": "sensor_create",
        "description": "Create a sensor on a parent object and configure a simple cone.",
        "parameters": {
            "type": "object",
            "properties": {
                "parent_name": {
                    "type": "string",
                    "description": "Parent satellite/facility name"
                },
                "sensor_name": {
                    "type": "string",
                    "description": "Sensor name"
                },
                "pattern": {
                    "type": "string",
                    "description": "Sensor pattern",
                    "enum": [
                        "ComplexConic",
                        "Custom",
                        "HalfPower",
                        "Rectangular",
                        "SAR",
                        "SimpleCone",
                        "EOIR"
                    ],
                    "default": "SimpleCone"
                },
                "cone_angle_deg": {
                    "type": "number",
                    "description": "Simple-cone half angle (deg)",
                    "default": 10.0,
                    "minimum": 0.001,
                    "maximum": 180
                },
                "replace_existing": {
                    "type": "boolean",
                    "description": "Unload an existing sensor",
                    "default": false
                }
            },
            "additionalProperties": false,
            "required": [
                "parent_name",
                "sensor_name"
            ]
        },
        "category": "sensor",
        "mutating": true
    },
    {
        "name": "stk_sensor_set_cone",
        "operation": "sensor_set_cone",
        "description": "Set the half-angle of a SimpleCone sensor.",
        "parameters": {
            "type": "object",
            "properties": {
                "parent_name": {
                    "type": "string",
                    "description": "Parent object name"
                },
                "sensor_name": {
                    "type": "string",
                    "description": "Sensor name"
                },
                "cone_angle_deg": {
                    "type": "number",
                    "description": "Cone half-angle (deg)",
                    "minimum": 0.001,
                    "maximum": 180
                }
            },
            "additionalProperties": false,
            "required": [
                "parent_name",
                "sensor_name",
                "cone_angle_deg"
            ]
        },
        "category": "sensor",
        "mutating": true
    },
    {
        "name": "stk_sensor_list",
        "operation": "sensor_list",
        "description": "List sensors, optionally limited to one parent object.",
        "parameters": {
            "type": "object",
            "properties": {
                "parent_name": {
                    "type": "string",
                    "description": "Optional parent object name"
                }
            },
            "additionalProperties": false
        },
        "category": "sensor",
        "mutating": false
    },
    {
        "name": "stk_constellation_create",
        "operation": "constellation_create",
        "description": "Create a constellation and optionally add satellites to it.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Constellation name"
                },
                "objects": {
                    "type": "array",
                    "description": "Object names/paths to add",
                    "default": [],
                    "items": {
                        "type": "string"
                    }
                },
                "replace_existing": {
                    "type": "boolean",
                    "description": "Unload an existing constellation",
                    "default": false
                }
            },
            "additionalProperties": false,
            "required": [
                "name"
            ]
        },
        "category": "constellation",
        "mutating": true
    },
    {
        "name": "stk_constellation_add_object",
        "operation": "constellation_add_object",
        "description": "Add a satellite/object to a constellation.",
        "parameters": {
            "type": "object",
            "properties": {
                "constellation_name": {
                    "type": "string",
                    "description": "Constellation name"
                },
                "object_name": {
                    "type": "string",
                    "description": "Object name or path"
                }
            },
            "additionalProperties": false,
            "required": [
                "constellation_name",
                "object_name"
            ]
        },
        "category": "constellation",
        "mutating": true
    },
    {
        "name": "stk_constellation_list",
        "operation": "constellation_list",
        "description": "List constellations and their members.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": false
        },
        "category": "constellation",
        "mutating": false
    },
    {
        "name": "stk_constellation_build_walker",
        "operation": "constellation_build_walker",
        "description": "Batch-build a Walker Delta/Star constellation from circular orbits and add all generated satellites to a constellation object.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Constellation name"
                },
                "total_sats": {
                    "type": "integer",
                    "description": "Total satellites (1-200)",
                    "default": 12,
                    "minimum": 1,
                    "maximum": 200
                },
                "planes": {
                    "type": "integer",
                    "description": "Number of orbital planes",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 200
                },
                "pattern": {
                    "type": "string",
                    "description": "Walker pattern: delta (360° RAAN spread) or star (180°)",
                    "enum": [
                        "walker_delta",
                        "walker_star"
                    ],
                    "default": "walker_delta"
                },
                "altitude_km": {
                    "type": "number",
                    "description": "Circular altitude (km)",
                    "default": 550,
                    "minimum": 0
                },
                "inclination_deg": {
                    "type": "number",
                    "description": "Inclination (deg)",
                    "default": 53,
                    "minimum": 0,
                    "maximum": 180
                },
                "phasing": {
                    "type": "integer",
                    "description": "Walker phasing factor F",
                    "default": 0,
                    "minimum": 0,
                    "maximum": 199
                },
                "raan0_deg": {
                    "type": "number",
                    "description": "RAAN of the first plane (deg)",
                    "default": 0
                },
                "mean_anomaly0_deg": {
                    "type": "number",
                    "description": "Mean anomaly of the first satellite (deg)",
                    "default": 0
                },
                "epoch": {
                    "type": "string",
                    "description": "Optional orbit epoch"
                },
                "propagator": {
                    "type": "string",
                    "description": "Propagator",
                    "enum": [
                        "TwoBody",
                        "J2Perturbation",
                        "J4Perturbation",
                        "HPOP"
                    ],
                    "default": "TwoBody"
                },
                "name_prefix": {
                    "type": "string",
                    "description": "Satellite name prefix",
                    "default": "Sat"
                },
                "replace_existing": {
                    "type": "boolean",
                    "description": "Unload an existing constellation with this name",
                    "default": false
                }
            },
            "additionalProperties": false,
            "required": [
                "name",
                "total_sats",
                "planes"
            ]
        },
        "category": "constellation",
        "mutating": true
    },
    {
        "name": "stk_chain_create",
        "operation": "chain_create",
        "description": "Create an access chain and optionally add objects to it.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Chain name"
                },
                "objects": {
                    "type": "array",
                    "description": "Object names/paths",
                    "default": [],
                    "items": {
                        "type": "string"
                    }
                },
                "replace_existing": {
                    "type": "boolean",
                    "description": "Unload an existing chain",
                    "default": false
                }
            },
            "additionalProperties": false,
            "required": [
                "name"
            ]
        },
        "category": "chain",
        "mutating": true
    },
    {
        "name": "stk_chain_add_object",
        "operation": "chain_add_object",
        "description": "Append an object to an access chain.",
        "parameters": {
            "type": "object",
            "properties": {
                "chain_name": {
                    "type": "string",
                    "description": "Chain name"
                },
                "object_name": {
                    "type": "string",
                    "description": "Object name or path"
                }
            },
            "additionalProperties": false,
            "required": [
                "chain_name",
                "object_name"
            ]
        },
        "category": "chain",
        "mutating": true
    },
    {
        "name": "stk_chain_compute_access",
        "operation": "chain_compute_access",
        "description": "Compute access through a chain and return the computed strand intervals.",
        "parameters": {
            "type": "object",
            "properties": {
                "chain_name": {
                    "type": "string",
                    "description": "Chain name"
                }
            },
            "additionalProperties": false,
            "required": [
                "chain_name"
            ]
        },
        "category": "chain",
        "mutating": true
    },
    {
        "name": "stk_platform_create",
        "operation": "platform_create",
        "description": "Create an aircraft, ship or ground vehicle.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Platform name"
                },
                "platform_type": {
                    "type": "string",
                    "description": "Platform class",
                    "enum": [
                        "Aircraft",
                        "Ship",
                        "GroundVehicle"
                    ]
                },
                "replace_existing": {
                    "type": "boolean",
                    "description": "Unload an existing platform",
                    "default": false
                }
            },
            "additionalProperties": false,
            "required": [
                "name",
                "platform_type"
            ]
        },
        "category": "platform",
        "mutating": true
    },
    {
        "name": "stk_platform_list",
        "operation": "platform_list",
        "description": "List aircraft, ships and ground vehicles in the scenario.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": false
        },
        "category": "platform",
        "mutating": false
    },
    {
        "name": "stk_platform_set_waypoints",
        "operation": "platform_set_waypoints",
        "description": "Set a time-specified great-arc route for an aircraft, ship or ground vehicle and propagate it.",
        "parameters": {
            "type": "object",
            "properties": {
                "platform_name": {
                    "type": "string",
                    "description": "Platform name"
                },
                "waypoints": {
                    "type": "array",
                    "description": "Waypoints in time order",
                    "items": {
                        "type": "object",
                        "additionalProperties": false,
                        "properties": {
                            "time": {
                                "type": "string",
                                "description": "Waypoint time (UTCG/ISO)"
                            },
                            "latitude_deg": {
                                "type": "number",
                                "description": "Latitude (-90..90)"
                            },
                            "longitude_deg": {
                                "type": "number",
                                "description": "Longitude (-180..180)"
                            },
                            "altitude_km": {
                                "type": "number",
                                "description": "Altitude (km)"
                            },
                            "turn_radius_km": {
                                "type": "number",
                                "description": "Turn radius (km)"
                            }
                        },
                        "required": [
                            "time",
                            "latitude_deg",
                            "longitude_deg"
                        ]
                    }
                }
            },
            "additionalProperties": false,
            "required": [
                "platform_name",
                "waypoints"
            ]
        },
        "category": "platform",
        "mutating": true
    },
    {
        "name": "stk_platform_state",
        "operation": "platform_state",
        "description": "Query an aircraft/ship/ground-vehicle position at a time.",
        "parameters": {
            "type": "object",
            "properties": {
                "platform_name": {
                    "type": "string",
                    "description": "Platform name"
                },
                "time": {
                    "type": "string",
                    "description": "Query time (defaults to scenario start)"
                }
            },
            "additionalProperties": false,
            "required": [
                "platform_name"
            ]
        },
        "category": "platform",
        "mutating": false
    },
    {
        "name": "stk_object_set_graphics",
        "operation": "object_set_graphics",
        "description": "Set 2D graphics attributes such as visibility, label, marker and line style.",
        "parameters": {
            "type": "object",
            "properties": {
                "object_name": {
                    "type": "string",
                    "description": "Object name"
                },
                "visible": {
                    "type": "boolean",
                    "description": "Object visibility"
                },
                "label_visible": {
                    "type": "boolean",
                    "description": "Label visibility"
                },
                "marker_style": {
                    "type": "string",
                    "description": "Marker style name"
                },
                "line_style": {
                    "type": "string",
                    "description": "Line style name"
                }
            },
            "additionalProperties": false,
            "required": [
                "object_name"
            ]
        },
        "category": "graphics",
        "mutating": true
    },
    {
        "name": "stk_object_get_graphics",
        "operation": "object_get_graphics",
        "description": "Read the main 2D graphics attributes of an object.",
        "parameters": {
            "type": "object",
            "properties": {
                "object_name": {
                    "type": "string",
                    "description": "Object name"
                }
            },
            "additionalProperties": false,
            "required": [
                "object_name"
            ]
        },
        "category": "graphics",
        "mutating": false
    },
    {
        "name": "stk_satellite_create",
        "operation": "satellite_create",
        "description": "Create a satellite in the current scenario and select a propagator.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Satellite name"
                },
                "propagator": {
                    "type": "string",
                    "description": "Propagator type",
                    "enum": [
                        "TwoBody",
                        "J2Perturbation",
                        "J4Perturbation",
                        "HPOP",
                        "SGP4",
                        "Astrogator",
                        "StkExternal"
                    ],
                    "default": "TwoBody"
                },
                "replace_existing": {
                    "type": "boolean",
                    "description": "Unload an existing satellite with the same name",
                    "default": false
                }
            },
            "additionalProperties": false,
            "required": [
                "name"
            ]
        },
        "category": "satellite",
        "mutating": true
    },
    {
        "name": "stk_satellite_set_orbit",
        "operation": "satellite_set_orbit",
        "description": "Define a satellite orbit from classical elements, a Cartesian state, TLE lines, or an ephemeris file, then propagate it.",
        "parameters": {
            "type": "object",
            "properties": {
                "satellite_name": {
                    "type": "string",
                    "description": "Satellite name"
                },
                "mode": {
                    "type": "string",
                    "description": "Orbit representation",
                    "enum": [
                        "classical",
                        "cartesian",
                        "tle",
                        "from_file"
                    ],
                    "default": "classical"
                },
                "semi_major_axis_km": {
                    "type": "number",
                    "description": "Classical: semi-major axis (km)",
                    "minimum": 1
                },
                "eccentricity": {
                    "type": "number",
                    "description": "Classical: eccentricity (0-1)",
                    "minimum": 0,
                    "maximum": 0.999999
                },
                "inclination_deg": {
                    "type": "number",
                    "description": "Classical: inclination (deg)",
                    "minimum": 0,
                    "maximum": 180
                },
                "raan_deg": {
                    "type": "number",
                    "description": "Classical: right ascension of ascending node (deg)"
                },
                "arg_of_perigee_deg": {
                    "type": "number",
                    "description": "Classical: argument of perigee (deg)"
                },
                "mean_anomaly_deg": {
                    "type": "number",
                    "description": "Classical: mean anomaly at epoch (deg)"
                },
                "epoch": {
                    "type": "string",
                    "description": "Orbit epoch (IO-8601 or STK UTCG)"
                },
                "coordinate_system": {
                    "type": "string",
                    "description": "Classical/Cartesian coordinate system",
                    "enum": [
                        "AlignmentAtEpoch",
                        "B1950",
                        "Fixed",
                        "J2000",
                        "MeanOfDate",
                        "MeanOfEpoch",
                        "TEMEOfDate",
                        "TEMEOfEpoch",
                        "TrueOfDate",
                        "TrueOfEpoch",
                        "TrueOfRefDate",
                        "ICRF"
                    ],
                    "default": "J2000"
                },
                "x_km": {
                    "type": "number",
                    "description": "Cartesian: X position (km)"
                },
                "y_km": {
                    "type": "number",
                    "description": "Cartesian: Y position (km)"
                },
                "z_km": {
                    "type": "number",
                    "description": "Cartesian: Z position (km)"
                },
                "vx_km_s": {
                    "type": "number",
                    "description": "Cartesian: X velocity (km/s)"
                },
                "vy_km_s": {
                    "type": "number",
                    "description": "Cartesian: Y velocity (km/s)"
                },
                "vz_km_s": {
                    "type": "number",
                    "description": "Cartesian: Z velocity (km/s)"
                },
                "tle_line1": {
                    "type": "string",
                    "description": "TLE: line 1"
                },
                "tle_line2": {
                    "type": "string",
                    "description": "TLE: line 2"
                },
                "file_path": {
                    "type": "string",
                    "description": "From-file: ephemeris file path"
                },
                "propagate": {
                    "type": "boolean",
                    "description": "Propagate after assigning the state",
                    "default": true
                }
            },
            "additionalProperties": false,
            "required": [
                "satellite_name"
            ]
        },
        "category": "satellite",
        "mutating": true
    },
    {
        "name": "stk_satellite_propagate",
        "operation": "satellite_propagate",
        "description": "Propagate the satellite ephemeris to the scenario time interval.",
        "parameters": {
            "type": "object",
            "properties": {
                "satellite_name": {
                    "type": "string",
                    "description": "Satellite name"
                },
                "use_scenario_time": {
                    "type": "boolean",
                    "description": "Use the scenario analysis interval",
                    "default": true
                }
            },
            "additionalProperties": false,
            "required": [
                "satellite_name"
            ]
        },
        "category": "satellite",
        "mutating": true
    },
    {
        "name": "stk_satellite_state",
        "operation": "satellite_state",
        "description": "Query a satellite's Cartesian position/velocity, LLA and classical elements at a specific time or at the scenario start.",
        "parameters": {
            "type": "object",
            "properties": {
                "satellite_name": {
                    "type": "string",
                    "description": "Satellite name"
                },
                "time": {
                    "type": "string",
                    "description": "Query time (defaults to scenario start)"
                },
                "frame": {
                    "type": "string",
                    "description": "Cartesian frame group",
                    "enum": [
                        "ICRF",
                        "J2000",
                        "Fixed",
                        "TrueOfDate",
                        "MeanOfDate"
                    ],
                    "default": "ICRF"
                }
            },
            "additionalProperties": false,
            "required": [
                "satellite_name"
            ]
        },
        "category": "analysis",
        "mutating": false
    },
    {
        "name": "stk_satellite_tle_summary",
        "operation": "satellite_tle_summary",
        "description": "Read the TLE summary data provider for a satellite (epoch, elements, validity).",
        "parameters": {
            "type": "object",
            "properties": {
                "satellite_name": {
                    "type": "string",
                    "description": "Satellite name"
                },
                "max_rows": {
                    "type": "integer",
                    "description": "Maximum rows",
                    "default": 50
                }
            },
            "additionalProperties": false,
            "required": [
                "satellite_name"
            ]
        },
        "category": "analysis",
        "mutating": false
    },
    {
        "name": "stk_satellite_ephemeris",
        "operation": "satellite_ephemeris",
        "description": "Sample a satellite ephemeris over an interval and optionally write a CSV file.",
        "parameters": {
            "type": "object",
            "properties": {
                "satellite_name": {
                    "type": "string",
                    "description": "Satellite name"
                },
                "start_time": {
                    "type": "string",
                    "description": "Start time (defaults to scenario start)"
                },
                "stop_time": {
                    "type": "string",
                    "description": "Stop time (defaults to scenario stop)"
                },
                "step_sec": {
                    "type": "number",
                    "description": "Sampling step in seconds",
                    "default": 60
                },
                "frame": {
                    "type": "string",
                    "description": "Cartesian frame group",
                    "enum": [
                        "ICRF",
                        "J2000",
                        "Fixed",
                        "TrueOfDate",
                        "MeanOfDate"
                    ],
                    "default": "ICRF"
                },
                "include_lla": {
                    "type": "boolean",
                    "description": "Also include LLA columns",
                    "default": true
                },
                "output_path": {
                    "type": "string",
                    "description": "Optional CSV output path"
                },
                "max_rows": {
                    "type": "integer",
                    "description": "Maximum returned rows",
                    "default": 2000
                }
            },
            "additionalProperties": false,
            "required": [
                "satellite_name"
            ]
        },
        "category": "analysis",
        "mutating": false
    },
    {
        "name": "stk_astrogator_summary",
        "operation": "astrogator_summary",
        "description": "List the Astrogator main-sequence segments for a satellite.",
        "parameters": {
            "type": "object",
            "properties": {
                "satellite_name": {
                    "type": "string",
                    "description": "Satellite name"
                }
            },
            "additionalProperties": false,
            "required": [
                "satellite_name"
            ]
        },
        "category": "astrogator",
        "mutating": false
    },
    {
        "name": "stk_astrogator_run",
        "operation": "astrogator_run",
        "description": "Run the Astrogator main sequence (RunMCS) and return the resulting state.",
        "parameters": {
            "type": "object",
            "properties": {
                "satellite_name": {
                    "type": "string",
                    "description": "Satellite name"
                }
            },
            "additionalProperties": false,
            "required": [
                "satellite_name"
            ]
        },
        "category": "astrogator",
        "mutating": true
    },
    {
        "name": "stk_satellite_set_propagator",
        "operation": "satellite_set_propagator",
        "description": "Change the propagator of an existing satellite (TwoBody, J2, J4, HPOP, SGP4).",
        "parameters": {
            "type": "object",
            "properties": {
                "satellite_name": {
                    "type": "string",
                    "description": "Satellite name"
                },
                "propagator": {
                    "type": "string",
                    "description": "New propagator",
                    "enum": [
                        "TwoBody",
                        "J2Perturbation",
                        "J4Perturbation",
                        "HPOP",
                        "SGP4"
                    ]
                }
            },
            "additionalProperties": false,
            "required": [
                "satellite_name",
                "propagator"
            ]
        },
        "category": "satellite",
        "mutating": true
    },
    {
        "name": "stk_satellite_list",
        "operation": "satellite_list",
        "description": "List satellites in the current scenario.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": false
        },
        "category": "satellite",
        "mutating": false
    },
    {
        "name": "stk_scenario_create",
        "operation": "scenario_create",
        "description": "Create a new STK scenario. Closes the open scenario only when replace_existing=true; otherwise it fails rather than silently discarding work.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Scenario name"
                },
                "start_time": {
                    "type": "string",
                    "description": "Start epoch (ISO-8601 or STK UTCG). Defaults to the current UTC minute."
                },
                "stop_time": {
                    "type": "string",
                    "description": "Stop epoch (ISO-8601 or STK UTCG)"
                },
                "duration_hours": {
                    "type": "number",
                    "description": "Duration used when stop_time is omitted",
                    "default": 24.0
                },
                "description": {
                    "type": "string",
                    "description": "Optional scenario description"
                },
                "path": {
                    "type": "string",
                    "description": "Optional .sc path. Saving requires confirm_save=true and an ASCII-only path."
                },
                "confirm_save": {
                    "type": "boolean",
                    "description": "Explicit user approval to save; never set true without asking the user",
                    "default": false
                },
                "replace_existing": {
                    "type": "boolean",
                    "description": "Close an already-open scenario first",
                    "default": false
                }
            },
            "additionalProperties": false,
            "required": [
                "name"
            ]
        },
        "category": "scenario",
        "mutating": true
    },
    {
        "name": "stk_scenario_open",
        "operation": "scenario_open",
        "description": "Open an existing .sc scenario file.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute or relative path to a .sc file"
                },
                "replace_existing": {
                    "type": "boolean",
                    "description": "Close an already-open scenario first",
                    "default": true
                }
            },
            "additionalProperties": false,
            "required": [
                "path"
            ]
        },
        "category": "scenario",
        "mutating": true
    },
    {
        "name": "stk_scenario_save",
        "operation": "scenario_save",
        "description": "Save the current scenario in place or to a new .sc path. Requires explicit confirm_save=true; without a path it uses STK's default scenario location. Paths must be ASCII-only (no Chinese characters).",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Save-as path; omit to save in STK's default location"
                },
                "confirm_save": {
                    "type": "boolean",
                    "description": "Explicit user approval to save; never set true without asking the user",
                    "default": false
                },
                "overwrite": {
                    "type": "boolean",
                    "description": "Allow replacing an existing save-as file",
                    "default": true
                }
            },
            "additionalProperties": false
        },
        "category": "scenario",
        "mutating": true
    },
    {
        "name": "stk_scenario_close",
        "operation": "scenario_close",
        "description": "Close the current scenario without quitting STK.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": false
        },
        "category": "scenario",
        "mutating": true
    },
    {
        "name": "stk_scenario_info",
        "operation": "scenario_info",
        "description": "Return the current scenario name, time period, duration and top-level objects.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": false
        },
        "category": "scenario",
        "mutating": false
    },
    {
        "name": "stk_scenario_set_time",
        "operation": "scenario_set_time",
        "description": "Update the scenario start/stop time (or extend by duration_hours).",
        "parameters": {
            "type": "object",
            "properties": {
                "start_time": {
                    "type": "string",
                    "description": "New start epoch"
                },
                "stop_time": {
                    "type": "string",
                    "description": "New stop epoch"
                },
                "duration_hours": {
                    "type": "number",
                    "description": "Duration from start when stop is omitted"
                }
            },
            "additionalProperties": false
        },
        "category": "scenario",
        "mutating": true
    }
];
