from __future__ import annotations

from dataclasses import dataclass

CORE_T0_K = 300.0
DEFAULT_DATASET_NAME = "wrfout_d01_2015-04-17_18_00_00_corte"
DEFAULT_OUTPUT_DIR_NAME = "outputs"

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
    "approximate thermodynamics are deferred because PB is absent",
)

LIMITATIONS = (
    "PB is absent, so exact pressure and exact temperature reconstruction are not possible.",
    "PH, PHB and HGT are absent, so geometric altitude products are out of scope for phase 1.",
    "The phase-2 liquid mask is a horizontal binary proxy and does not yet estimate icing severity.",
)

ASSUMPTIONS = (
    "T is interpreted as perturbation potential temperature and theta is recovered as T + 300 K.",
    "Vertical results are expressed in model levels or eta-relative coordinates, not in meters or feet.",
    "The first phase is a reproducible script pipeline instead of a notebook-first workflow.",
)


@dataclass(frozen=True, slots=True)
class DiagnosticStatus:
    name: str
    status: str
    reason: str

