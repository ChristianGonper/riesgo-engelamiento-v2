from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import xarray as xr

from .config import ASSUMPTIONS, CORE_T0_K, LIMITATIONS, DiagnosticStatus
from .dataset import ValidationReport


@dataclass(frozen=True, slots=True)
class Phase1Summary:
    dataset_path: Path
    title: str | None
    start_date: str | None
    time_count: int
    time_start: str | None
    time_end: str | None
    time_step_minutes: int | None
    horizontal_shape: tuple[int, int]
    vertical_levels: int
    vertical_staggered_levels: int
    validation: ValidationReport
    assumptions: tuple[str, ...]
    limitations: tuple[str, ...]
    diagnostics: tuple[DiagnosticStatus, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_path": str(self.dataset_path),
            "title": self.title,
            "start_date": self.start_date,
            "time_count": self.time_count,
            "time_start": self.time_start,
            "time_end": self.time_end,
            "time_step_minutes": self.time_step_minutes,
            "horizontal_shape": list(self.horizontal_shape),
            "vertical_levels": self.vertical_levels,
            "vertical_staggered_levels": self.vertical_staggered_levels,
            "validation": self.validation.to_dict(),
            "assumptions": list(self.assumptions),
            "limitations": list(self.limitations),
            "diagnostics": [asdict(diagnostic) for diagnostic in self.diagnostics],
        }

    def to_markdown(self) -> str:
        lines = [
            "# Fase 1: validacion base del dataset WRF",
            "",
            f"- Dataset: `{self.dataset_path}`",
            f"- Title: {self.title or 'unknown'}",
            f"- Start date: {self.start_date or 'unknown'}",
            f"- Times: {self.time_count}",
            f"- Time span: {self.time_start or 'unknown'} -> {self.time_end or 'unknown'}",
            f"- Time step: {self.time_step_minutes if self.time_step_minutes is not None else 'unknown'} minutes",
            f"- Horizontal grid: {self.horizontal_shape[0]} x {self.horizontal_shape[1]}",
            f"- Vertical levels: {self.vertical_levels}",
            f"- Staggered vertical levels: {self.vertical_staggered_levels}",
            "",
            "## Diagnostic status",
        ]
        for diagnostic in self.diagnostics:
            lines.append(f"- {diagnostic.name}: {diagnostic.status} ({diagnostic.reason})")
        lines.extend(
            [
                "",
                "## Assumptions",
            ]
        )
        for assumption in self.assumptions:
            lines.append(f"- {assumption}")
        lines.extend(
            [
                "",
                "## Limitations",
            ]
        )
        for limitation in self.limitations:
            lines.append(f"- {limitation}")
        lines.extend(["", f"## Core constant", f"- T0 = {CORE_T0_K:.0f} K", ""])
        lines.append(self.validation.to_markdown())
        return "\n".join(lines)


def _coerce_time_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, np.datetime64):
        return np.datetime_as_string(value, unit="s")
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")
    return str(value)


def _coerce_text_attr(value: Any) -> str | None:
    if value is None:
        return None
    return str(value).strip()


def _infer_time_step_minutes(time_values: np.ndarray) -> int | None:
    if time_values.size < 2:
        return None
    deltas = np.diff(time_values).astype("timedelta64[m]")
    first = int(deltas[0].astype(int))
    if np.all(deltas == deltas[0]):
        return first
    return None


def _build_diagnostics(dataset: xr.Dataset, validation: ValidationReport) -> tuple[DiagnosticStatus, ...]:
    missing_variables = set(validation.missing_variables)
    missing_dimensions = set(validation.missing_dimensions)

    def _status_for(required_variables: set[str], required_dimensions: set[str] = set()) -> tuple[str, str]:
        absent_variables = sorted(required_variables & missing_variables)
        absent_dimensions = sorted(required_dimensions & missing_dimensions)
        if absent_variables or absent_dimensions:
            parts: list[str] = []
            if absent_variables:
                parts.append(f"missing variables: {', '.join(absent_variables)}")
            if absent_dimensions:
                parts.append(f"missing dimensions: {', '.join(absent_dimensions)}")
            return "unsupported", "; ".join(parts)
        return "supported", "all required inputs are present."

    diagnostics: list[DiagnosticStatus] = []
    liquid_status, liquid_reason = _status_for({"QCLOUD", "QRAIN"})
    diagnostics.append(
        DiagnosticStatus(
            name="Liquid-water presence",
            status=liquid_status,
            reason=liquid_reason,
        )
    )
    vertical_status, vertical_reason = _status_for({"ZNW"}, {"bottom_top", "bottom_top_stag"})
    diagnostics.append(
        DiagnosticStatus(
            name="Vertical structure",
            status=vertical_status,
            reason=vertical_reason,
        )
    )
    mixed_status, mixed_reason = _status_for({"QICE"})
    diagnostics.append(
        DiagnosticStatus(
            name="Mixed-phase context",
            status=mixed_status,
            reason=mixed_reason,
        )
    )
    if {"T", "P", "ZNW"} & missing_variables:
        diagnostics.append(
            DiagnosticStatus(
                name="Approximate icing risk",
                status="unsupported",
                reason="missing required inputs for the future approximate path: T, P and ZNW must all be present.",
            )
        )
    elif "PB" in dataset:
        diagnostics.append(
            DiagnosticStatus(
                name="Approximate icing risk",
                status="available with caveats",
                reason="PB is present, so thermodynamic reconstruction can be improved later.",
            )
        )
    else:
        diagnostics.append(
            DiagnosticStatus(
                name="Approximate icing risk",
                status="available with caveats",
                reason="PB is absent, so the phase-5 risk product remains approximate and must use T + 300, P and ZNW as a proxy path.",
            )
        )
    severity_required = {"QCLOUD", "QRAIN", "QICE", "T", "P", "ZNW"}
    severity_missing = sorted(severity_required & missing_variables)
    if severity_missing:
        diagnostics.append(
            DiagnosticStatus(
                name="Phase 6 heuristic severity",
                status="unsupported",
                reason=f"missing required inputs for the phase-6 heuristic layer: {', '.join(severity_missing)}.",
            )
        )
    else:
        diagnostics.append(
            DiagnosticStatus(
                name="Phase 6 heuristic severity",
                status="available with caveats",
                reason="severity is available as a documented phase-6 heuristic built on the approximate risk product and relative model levels.",
            )
        )
    return tuple(diagnostics)


def build_phase1_summary(dataset: xr.Dataset, validation: ValidationReport, dataset_path: str | Path) -> Phase1Summary:
    times = dataset["XTIME"].values if "XTIME" in dataset else np.array([], dtype="datetime64[ns]")
    time_count = int(times.size)
    time_start = _coerce_time_value(times[0]) if time_count else None
    time_end = _coerce_time_value(times[-1]) if time_count else None
    time_step_minutes = _infer_time_step_minutes(times) if time_count else None
    horizontal_shape = (
        int(dataset.sizes.get("south_north", 0)),
        int(dataset.sizes.get("west_east", 0)),
    )
    vertical_levels = int(dataset.sizes.get("bottom_top", 0))
    vertical_staggered_levels = int(dataset.sizes.get("bottom_top_stag", 0))

    return Phase1Summary(
        dataset_path=Path(dataset_path),
        title=_coerce_text_attr(dataset.attrs.get("TITLE")),
        start_date=_coerce_text_attr(dataset.attrs.get("START_DATE")),
        time_count=time_count,
        time_start=time_start,
        time_end=time_end,
        time_step_minutes=time_step_minutes,
        horizontal_shape=horizontal_shape,
        vertical_levels=vertical_levels,
        vertical_staggered_levels=vertical_staggered_levels,
        validation=validation,
        assumptions=ASSUMPTIONS,
        limitations=LIMITATIONS,
        diagnostics=_build_diagnostics(dataset, validation),
    )


def write_phase1_outputs(summary: Phase1Summary, output_dir: str | Path) -> tuple[Path, Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    markdown_path = output_path / "phase1_summary.md"
    json_path = output_path / "phase1_summary.json"
    markdown_path.write_text(summary.to_markdown(), encoding="utf-8")
    json_path.write_text(json.dumps(summary.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return markdown_path, json_path
