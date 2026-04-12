from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import xarray as xr

from .config import EXPECTED_DIMENSIONS, EXPECTED_DIMS_BY_VARIABLE, REQUIRED_VARIABLES


@dataclass(frozen=True, slots=True)
class ValidationReport:
    source: Path | None
    present_variables: tuple[str, ...]
    missing_variables: tuple[str, ...]
    present_dimensions: dict[str, int]
    missing_dimensions: tuple[str, ...]
    variable_dimension_issues: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_valid(self) -> bool:
        return not self.missing_variables and not self.missing_dimensions and not self.variable_dimension_issues

    def error_message(self) -> str:
        problems: list[str] = []
        if self.missing_variables:
            problems.append(f"Missing required variables: {', '.join(self.missing_variables)}")
        if self.missing_dimensions:
            problems.append(f"Missing required dimensions: {', '.join(self.missing_dimensions)}")
        problems.extend(self.variable_dimension_issues)
        return "; ".join(problems) if problems else "No validation problems found."

    def to_markdown(self) -> str:
        lines = ["## Validation", ""]
        if self.source is not None:
            lines.append(f"- Source: `{self.source}`")
        lines.append(f"- Status: {'valid' if self.is_valid else 'invalid'}")
        lines.append(f"- Present variables: {', '.join(self.present_variables)}")
        lines.append(f"- Missing variables: {', '.join(self.missing_variables) if self.missing_variables else 'none'}")
        lines.append(f"- Present dimensions: {', '.join(f'{name}={size}' for name, size in self.present_dimensions.items())}")
        lines.append(f"- Missing dimensions: {', '.join(self.missing_dimensions) if self.missing_dimensions else 'none'}")
        if self.variable_dimension_issues:
            lines.append("- Dimension issues:")
            for issue in self.variable_dimension_issues:
                lines.append(f"  - {issue}")
        if self.warnings:
            lines.append("- Warnings:")
            for warning in self.warnings:
                lines.append(f"  - {warning}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": str(self.source) if self.source is not None else None,
            "present_variables": list(self.present_variables),
            "missing_variables": list(self.missing_variables),
            "present_dimensions": dict(self.present_dimensions),
            "missing_dimensions": list(self.missing_dimensions),
            "variable_dimension_issues": list(self.variable_dimension_issues),
            "warnings": list(self.warnings),
            "is_valid": self.is_valid,
        }


class DatasetValidationError(RuntimeError):
    pass


def open_dataset(path: str | Path) -> xr.Dataset:
    return xr.open_dataset(Path(path))


def validate_dataset(dataset: xr.Dataset, source: str | Path | None = None) -> ValidationReport:
    source_path = Path(source) if source is not None else None
    present_variables = tuple(name for name in REQUIRED_VARIABLES if name in dataset)
    missing_variables = tuple(name for name in REQUIRED_VARIABLES if name not in dataset)
    present_dimensions = {name: int(size) for name, size in dataset.sizes.items()}
    missing_dimensions = tuple(name for name in EXPECTED_DIMENSIONS if name not in dataset.sizes)

    variable_dimension_issues: list[str] = []
    for variable_name, expected_dims in EXPECTED_DIMS_BY_VARIABLE.items():
        if variable_name not in dataset:
            continue
        actual_dims = tuple(dataset[variable_name].dims)
        if actual_dims != expected_dims:
            variable_dimension_issues.append(
                f"{variable_name} dims are {actual_dims}, expected {expected_dims}"
            )

    if "Time" in dataset.sizes and "XTIME" in dataset and dataset["XTIME"].sizes.get("Time") != dataset.sizes["Time"]:
        variable_dimension_issues.append(
            f"XTIME length is {dataset['XTIME'].sizes.get('Time')} but Time dimension is {dataset.sizes['Time']}"
        )

    if {"bottom_top", "bottom_top_stag"}.issubset(dataset.sizes):
        if dataset.sizes["bottom_top_stag"] != dataset.sizes["bottom_top"] + 1:
            variable_dimension_issues.append(
                "bottom_top_stag must be exactly one level larger than bottom_top"
            )

    warnings: list[str] = []
    if "PB" not in dataset:
        warnings.append("PB is absent, so phase-5 thermodynamic reconstruction will remain approximate.")
    if not source_path:
        source_path = None

    return ValidationReport(
        source=source_path,
        present_variables=present_variables,
        missing_variables=missing_variables,
        present_dimensions=present_dimensions,
        missing_dimensions=missing_dimensions,
        variable_dimension_issues=tuple(variable_dimension_issues),
        warnings=tuple(warnings),
    )


def assert_valid(report: ValidationReport) -> None:
    if report.is_valid:
        return
    raise DatasetValidationError(report.error_message())

