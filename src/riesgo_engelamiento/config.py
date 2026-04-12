from __future__ import annotations

from dataclasses import dataclass

CORE_T0_K = 300.0
DEFAULT_DATASET_NAME = "wrfout_d01_2015-04-17_18_00_00_corte"
DEFAULT_OUTPUT_DIR_NAME = "outputs"
APPROXIMATE_PRESSURE_TOP_PA = 5000.0
APPROXIMATE_PRESSURE_SURFACE_PA = 100000.0
APPROXIMATE_POISSON_KAPPA = 0.286
APPROXIMATE_FREEZING_THRESHOLD_K = 273.15
HEURISTIC_SEVERITY_SCORE_THRESHOLDS = (20.0, 40.0, 60.0)
HEURISTIC_SEVERITY_WEIGHTS = {
    "risk_horizontal": 0.35,
    "liquid_horizontal": 0.20,
    "mixed_horizontal": 0.15,
    "vertical_span": 0.15,
    "persistence": 0.15,
}
HEURISTIC_VERTICAL_BANDS = (
    ("upper", 0.66, 1.0),
    ("middle", 0.33, 0.66),
    ("lower", 0.0, 0.33),
)
HEURISTIC_LEVEL_ACTIVITY_THRESHOLD = 0.05

REQUIRED_VARIABLES = (
    "QCLOUD",
    "QRAIN",
    "QICE",
    "T",
    "P",
    "ZNW",
    "XLAT",
    "XLONG",
    "XTIME",
)

EXPECTED_DIMENSIONS = (
    "Time",
    "bottom_top",
    "south_north",
    "west_east",
    "bottom_top_stag",
)

EXPECTED_DIMS_BY_VARIABLE = {
    "QCLOUD": ("Time", "bottom_top", "south_north", "west_east"),
    "QRAIN": ("Time", "bottom_top", "south_north", "west_east"),
    "QICE": ("Time", "bottom_top", "south_north", "west_east"),
    "T": ("Time", "bottom_top", "south_north", "west_east"),
    "P": ("Time", "bottom_top", "south_north", "west_east"),
    "ZNW": ("Time", "bottom_top_stag"),
    "XLAT": ("Time", "south_north", "west_east"),
    "XLONG": ("Time", "south_north", "west_east"),
    "XTIME": ("Time",),
}

SUPPORTED_DIAGNOSTICS = (
    "liquid-water presence from QCLOUD + QRAIN",
    "binary horizontal liquid mask for a selected time step",
    "ice-context support from QICE",
    "relative vertical structure in model levels / eta coordinates",
    "approximate thermodynamics and icing risk through the documented phase-5 eta proxy",
    "phase-6 heuristic severity classification from the approximate risk product",
)

LIMITATIONS = (
    "PB is absent, so exact pressure and exact temperature reconstruction are not possible; the phase-5 risk product uses an explicit proxy.",
    "PH, PHB and HGT are absent, so geometric altitude products are out of scope for phase 1.",
    "The phase-2 liquid mask is a horizontal binary proxy and does not yet estimate icing severity.",
    "The phase-6 severity product is heuristic and intentionally relative to model levels, persistence and mixed-phase context.",
)

ASSUMPTIONS = (
    "T is interpreted as perturbation potential temperature and theta is recovered as T + 300 K.",
    "The phase-5 pressure proxy interpolates between 1000 hPa and 50 hPa in eta coordinates and then adds the perturbation pressure P.",
    "Vertical results are expressed in model levels or eta-relative coordinates, not in meters or feet.",
    "The first phase is a reproducible script pipeline instead of a notebook-first workflow.",
    "The phase-6 severity classification uses documented thresholds on risk fraction, liquid fraction, mixed-phase context and persistence.",
)


@dataclass(frozen=True, slots=True)
class DiagnosticStatus:
    name: str
    status: str
    reason: str

