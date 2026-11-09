# spaceone-stk-mcp 工具目录

本文件由 `stk-mcp/scripts/export_tool_docs.py` 从 Python 注册表生成，请勿手工编辑。

- 产品版本：`1.0.0`
- 操作总数：**77**
- 分类：`access`, `data`, `analysis`, `report`, `animation`, `connection`, `coverage`, `equipment`, `objects`, `sensor`, `constellation`, `chain`, `platform`, `graphics`, `satellite`, `astrogator`, `scenario`
- 完整 JSON Schema：`stk-mcp/contracts/tools.json`

| 操作 | 分类 | 写操作 | 说明 |
|---|---|---|---|
| `access_compute` | access | 是 | Compute access intervals between two objects over the scenario interval. |
| `access_batch` | access | 是 | Compute access from one source object to several target objects. |
| `access_report` | access | 是 | Generate an STK access report (Access style) between two objects. |
| `access_set_constraint` | access | 是 | Set a minimum/maximum access constraint (for example ElevationAngle) on an object. |
| `access_clear_constraints` | access | 是 | Remove all access constraints from an object. |
| `data_provider_list` | data | 否 | List data providers and their groups for an object. |
| `data_provider_query` | data | 否 | Execute a data-provider query and return a table of results. Use a single time for an instant query or start/stop/step for a time series. |
| `lighting_compute` | analysis | 是 | Compute sunlight/eclipse intervals for an object. |
| `report_list_styles` | report | 否 | List available STK report styles (*.rst) from the installed STKData and the user's Config\Styles directories. Use a returned name as report_create.style. |
| `report_create` | report | 是 | Generate an STK report through ReportCreate and return the file path plus preview. |
| `animation_control` | animation | 是 | Control scenario animation: play, pause, stop, step, set_time or set_rate. |
| `animation_info` | animation | 否 | Read the current animation time, scenario time bounds and playback rate. |
| `scenario_set_view` | animation | 是 | Activate the 2D/3D graphics windows and optionally show all objects. |
| `stk_connect` | connection | 是 | Launch or attach to STK 11/12 through COM. Existing instances are reused; a new instance is started only when no STK automation object is running. |
| `stk_disconnect` | connection | 是 | Release the STK COM reference. Do NOT call this at the end of a modeling or analysis task: leave the scenario open for the user. The STK process is not quit and the scenario is not closed by default. |
| `stk_status` | connection | 否 | Report whether the kernel is connected, the STK version/PID and the open scenario. |
| `stk_capabilities` | connection | 否 | List the STK version, object types supported by the installed license, and the available Connect port. Useful before building a workflow. |
| `stk_execute_command` | connection | 是 | Execute a raw STK Connect command. transport=com uses the COM ExecuteCommand path; transport=tcp uses the Connect socket and returns raw reply data. |
| `stk_selftest` | connection | 是 | Run an end-to-end STK smoke test: scenario, satellite orbit, propagation, state query, facility, access, coverage and report. With an existing scenario open it performs read-only checks unless replace_scenario=true. |
| `coverage_create` | coverage | 是 | Create a coverage definition. |
| `coverage_set_grid` | coverage | 是 | Set a global or latitude/longitude coverage grid. |
| `coverage_add_asset` | coverage | 是 | Assign an object as a coverage asset. |
| `coverage_remove_asset` | coverage | 是 | Remove an asset from a coverage definition. |
| `coverage_compute` | coverage | 是 | Compute coverage accesses and return high-level coverage statistics. |
| `coverage_stats` | coverage | 否 | Read coverage statistics without recomputing accesses. |
| `coverage_fom_create` | coverage | 是 | Create a Figure of Merit under a coverage definition and optionally set its type. |
| `coverage_fom_query` | coverage | 否 | Query a figure-of-merit data provider. |
| `coverage_grid_inspector` | coverage | 是 | Select a grid point and read its point/region coverage values. |
| `equipment_create` | equipment | 是 | Create an antenna, receiver, transmitter or radar on a parent object. |
| `equipment_list` | equipment | 否 | List antennas, receivers, transmitters and radars on a parent object. |
| `equipment_delete` | equipment | 是 | Delete an antenna/receiver/transmitter/radar from its parent. |
| `equipment_configure` | equipment | 是 | Configure a transmitter (frequency/EIRP/data rate), antenna (design frequency/diameter) or receiver (G/T). Only writable model properties are applied; unsupported fields are returned in errors. |
| `object_list` | objects | 否 | List objects in the scenario, optionally filtered by class and including nested children such as sensors and equipment. |
| `object_info` | objects | 否 | Return detailed metadata for one object and optionally its children. |
| `object_delete` | objects | 是 | Unload an object from the scenario. |
| `facility_create` | objects | 是 | Create a ground facility at a geodetic position. |
| `facility_set_position` | objects | 是 | Move an existing facility. |
| `place_create` | objects | 是 | Create a point place at a geodetic position. |
| `place_set_position` | objects | 是 | Move an existing point place. |
| `area_target_create` | objects | 是 | Create a ground area target, optionally as an ellipse. |
| `area_target_set_ellipse` | objects | 是 | Configure an existing area target as an ellipse. |
| `area_target_set_polygon` | objects | 是 | Configure an existing area target as a polygon boundary from lat/lon points. |
| `area_target_add_boundary_point` | objects | 是 | Append one boundary point to an area target (switches it to polygon mode). |
| `target_set_position` | objects | 是 | Set a target position from geodetic coordinates or spherical (declination, right ascension, altitude). |
| `target_create` | objects | 是 | Create a celestial target object (star-like pointing target). |
| `sensor_create` | sensor | 是 | Create a sensor on a parent object and configure a simple cone. |
| `sensor_set_cone` | sensor | 是 | Set the half-angle of a SimpleCone sensor. |
| `sensor_list` | sensor | 否 | List sensors, optionally limited to one parent object. |
| `constellation_create` | constellation | 是 | Create a constellation and optionally add satellites to it. |
| `constellation_add_object` | constellation | 是 | Add a satellite/object to a constellation. |
| `constellation_list` | constellation | 否 | List constellations and their members. |
| `constellation_build_walker` | constellation | 是 | Batch-build a Walker Delta/Star constellation from circular orbits and add all generated satellites to a constellation object. |
| `chain_create` | chain | 是 | Create an access chain and optionally add objects to it. |
| `chain_add_object` | chain | 是 | Append an object to an access chain. |
| `chain_compute_access` | chain | 是 | Compute access through a chain and return the computed strand intervals. |
| `platform_create` | platform | 是 | Create an aircraft, ship or ground vehicle. |
| `platform_list` | platform | 否 | List aircraft, ships and ground vehicles in the scenario. |
| `platform_set_waypoints` | platform | 是 | Set a time-specified great-arc route for an aircraft, ship or ground vehicle and propagate it. |
| `platform_state` | platform | 否 | Query an aircraft/ship/ground-vehicle position at a time. |
| `object_set_graphics` | graphics | 是 | Set 2D graphics attributes such as visibility, label, marker and line style. |
| `object_get_graphics` | graphics | 否 | Read the main 2D graphics attributes of an object. |
| `satellite_create` | satellite | 是 | Create a satellite in the current scenario and select a propagator. |
| `satellite_set_orbit` | satellite | 是 | Define a satellite orbit from classical elements, a Cartesian state, TLE lines, or an ephemeris file, then propagate it. |
| `satellite_propagate` | satellite | 是 | Propagate the satellite ephemeris to the scenario time interval. |
| `satellite_state` | analysis | 否 | Query a satellite's Cartesian position/velocity, LLA and classical elements at a specific time or at the scenario start. |
| `satellite_tle_summary` | analysis | 否 | Read the TLE summary data provider for a satellite (epoch, elements, validity). |
| `satellite_ephemeris` | analysis | 否 | Sample a satellite ephemeris over an interval and optionally write a CSV file. |
| `astrogator_summary` | astrogator | 否 | List the Astrogator main-sequence segments for a satellite. |
| `astrogator_run` | astrogator | 是 | Run the Astrogator main sequence (RunMCS) and return the resulting state. |
| `satellite_set_propagator` | satellite | 是 | Change the propagator of an existing satellite (TwoBody, J2, J4, HPOP, SGP4). |
| `satellite_list` | satellite | 否 | List satellites in the current scenario. |
| `scenario_create` | scenario | 是 | Create a new STK scenario. Closes the open scenario only when replace_existing=true; otherwise it fails rather than silently discarding work. |
| `scenario_open` | scenario | 是 | Open an existing .sc scenario file. |
| `scenario_save` | scenario | 是 | Save the current scenario in place or to a new .sc path. Requires explicit confirm_save=true; without a path it uses STK's default scenario location. Paths must be ASCII-only (no Chinese characters). |
| `scenario_close` | scenario | 是 | Close the current scenario without quitting STK. |
| `scenario_info` | scenario | 否 | Return the current scenario name, time period, duration and top-level objects. |
| `scenario_set_time` | scenario | 是 | Update the scenario start/stop time (or extend by duration_hours). |
