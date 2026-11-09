"""STK COM enumeration values and string normalizers.

Values verified against the STK 11 and STK 12 type libraries shipped with this
machine (``AgStkObjects.dll``); both releases use the same values for the
enumerations below.
"""

from __future__ import annotations

from .errors import StkValidationError

# AgESTKObjectType
OBJECT_TYPE: dict[str, int] = {
    "AdvCat": 0,
    "Aircraft": 1,
    "AreaTarget": 2,
    "AttitudeCoverage": 3,
    "Chain": 4,
    "CommSystem": 5,
    "Constellation": 6,
    "CoverageDefinition": 7,
    "Facility": 8,
    "GroundVehicle": 9,
    "LaunchVehicle": 10,
    "LineTarget": 11,
    "MTO": 12,
    "Missile": 13,
    "MissileSystem": 14,
    "Planet": 15,
    "Radar": 16,
    "Receiver": 17,
    "Satellite": 18,
    "Scenario": 19,
    "Sensor": 20,
    "Ship": 21,
    "Star": 22,
    "Target": 23,
    "Transmitter": 24,
    "FigureOfMerit": 25,
    "Root": 26,
    "Access": 27,
    "ObjectCoverage": 28,
    "AttitudeFigureOfMerit": 29,
    "Submarine": 30,
    "Antenna": 31,
    "Place": 32,
    "Volumetric": 33,
}

# AgEVePropagatorType
PROPAGATOR_TYPE: dict[str, int] = {
    "HPOP": 0,
    "J2Perturbation": 1,
    "J4Perturbation": 2,
    "LOP": 3,
    "SGP4": 4,
    "SPICE": 5,
    "StkExternal": 6,
    "TwoBody": 7,
    "UserExternal": 8,
    "GreatArc": 9,
    "Ballistic": 10,
    "SimpleAscent": 11,
    "Astrogator": 12,
    "Realtime": 13,
    "GPS": 14,
    "Aviator": 15,
    "11Param": 16,
    "SP3": 17,
}

PROPAGATOR_ALIASES = {
    "two_body": "TwoBody",
    "twobody": "TwoBody",
    "j2": "J2Perturbation",
    "j4": "J4Perturbation",
    "hpop": "HPOP",
    "sgp4": "SGP4",
    "astrogator": "Astrogator",
}

# AgESnPattern
SENSOR_PATTERN: dict[str, int] = {
    "ComplexConic": 0,
    "Custom": 1,
    "HalfPower": 2,
    "Rectangular": 3,
    "SAR": 4,
    "SimpleCone": 5,
    "EOIR": 6,
}

# AgEClassicalLocation (kept for completeness; ``AssignClassical``'s last
# argument is the mean anomaly, so the kernel currently always uses mean
# anomaly semantics).
CLASSICAL_LOCATION: dict[str, int] = {
    "ArgumentOfLatitude": 0,
    "EccentricAnomaly": 1,
    "MeanAnomaly": 2,
    "TimePastAN": 3,
    "TimePastPerigee": 4,
    "TrueAnomaly": 5,
}

# First argument of IAgOrbitStateClassical.AssignClassical
# (AgECoordinateSystem in AgStkUtil.dll).
CLASSICAL_COORDINATE_SYSTEM: dict[str, int] = {
    "AlignmentAtEpoch": 0,
    "B1950": 1,
    "Fixed": 2,
    "J2000": 3,
    "MeanOfDate": 4,
    "MeanOfEpoch": 5,
    "TEMEOfDate": 6,
    "TEMEOfEpoch": 7,
    "TrueOfDate": 8,
    "TrueOfEpoch": 9,
    "TrueOfRefDate": 10,
    "ICRF": 11,
}

# AgEAccessConstraints
ACCESS_CONSTRAINT: dict[str, int] = {
    "ElevationAngle": 14,
    "AzimuthAngle": 6,
    "Range": 34,
    "Duration": 13,
    "BetaAngle": 8,
    "Altitude": 2,
    "Lighting": 25,
    "LineOfSight": 26,
    "GroundElevationAngle": 19,
    "SunElevationAngle": 58,
}


def normalize_enum(value: str, mapping: dict[str, int], label: str) -> int:
    if isinstance(value, int):
        if value in mapping.values():
            return value
        raise StkValidationError(f"Unknown {label} value: {value}")
    text = str(value).strip()
    for key, number in mapping.items():
        if key.lower() == text.lower():
            return number
    normalized = text.replace("_", "").replace("-", "").replace(" ", "").lower()
    for key, number in mapping.items():
        if key.replace("_", "").lower() == normalized:
            return number
    raise StkValidationError(
        f"Unknown {label} value: {value!r}",
        details={"allowed": sorted(mapping)},
    )


def normalize_propagator(value: str | None) -> str:
    if not value:
        return "TwoBody"
    text = str(value).strip()
    if text in PROPAGATOR_TYPE:
        return text
    lower = text.replace("_", "").replace("-", "").lower()
    for key in PROPAGATOR_TYPE:
        if key.lower() == lower:
            return key
    alias = PROPAGATOR_ALIASES.get(lower)
    if alias:
        return alias
    raise StkValidationError(
        f"Unknown propagator: {value!r}",
        details={"allowed": sorted(PROPAGATOR_TYPE)},
    )


def propagator_code(value: str | None) -> int:
    return PROPAGATOR_TYPE[normalize_propagator(value)]


def object_type_code(value: str) -> int:
    return normalize_enum(value, OBJECT_TYPE, "object type")


def sensor_pattern_code(value: str | None) -> int:
    return normalize_enum(value or "SimpleCone", SENSOR_PATTERN, "sensor pattern")


def access_constraint_code(value: str) -> int:
    return normalize_enum(value, ACCESS_CONSTRAINT, "access constraint")
