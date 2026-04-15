from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import xarray as xr

from .config import (
    APPROXIMATE_FREEZING_THRESHOLD_K,
    APPROXIMATE_POISSON_KAPPA,
    APPROXIMATE_PRESSURE_SURFACE_PA,
    APPROXIMATE_PRESSURE_TOP_PA,
    CORE_T0_K,
    HEURISTIC_LEVEL_ACTIVITY_THRESHOLD,
    HEURISTIC_SEVERITY_SCORE_THRESHOLDS,
    HEURISTIC_SEVERITY_WEIGHTS,
    HEURISTIC_VERTICAL_BANDS,
)
from .phase5 import build_phase5_approximate_risk_product

matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt  # noqa: E402


@dataclass(frozen=True, slots=True)
class SeverityBandSummary:
    name: str
    eta_min: float
    eta_max: float
    level_count: int
    active_level_count: int
    selected_risk_fraction: float
    selected_liquid_fraction: float
    selected_mixed_fraction: float
    mean_risk_fraction: float


@dataclass(frozen=True, slots=True)
class Phase4HeuristicSeverityProduct:
    dataset_path: Path
    time_index: int
    time_label: str | None
    horizontal_shape: tuple[int, int]
    vertical_levels: int
    eta_mid: xr.DataArray
    selected_liquid_level_fraction: xr.DataArray
    selected_ice_level_fraction: xr.DataArray
    selected_mixed_level_fraction: xr.DataArray
    selected_risk_level_fraction: xr.DataArray
    time_liquid_level_fraction: xr.DataArray
    time_ice_level_fraction: xr.DataArray
    time_mixed_level_fraction: xr.DataArray
    time_risk_level_fraction: xr.DataArray
    time_liquid_horizontal_fraction: xr.DataArray
    time_mixed_horizontal_fraction: xr.DataArray
    time_risk_horizontal_fraction: xr.DataArray
    time_active_level_fraction: xr.DataArray
    time_persistence_fraction: xr.DataArray
    severity_score_time: xr.DataArray
    severity_class_time: tuple[str, ...]
    severity_score: float
    severity_class: str
    persistence_fraction: float
    selected_active_level_ranges: tuple[str, ...]
    band_summaries: tuple[SeverityBandSummary, ...]
    dominant_band: str
    heuristic_notes: tuple[str, ...]

    def to_dict(
        self,
        output_paths: dict[str, Path] | None = None,
        *,
        phase_number: int = 4,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "dataset_path": str(self.dataset_path),
            "phase": phase_number,
            "product_kind": "heuristic proxy",
            "time_index": self.time_index,
            "time_label": self.time_label,
            "horizontal_shape": list(self.horizontal_shape),
            "vertical_levels": self.vertical_levels,
            "eta_mid": self.eta_mid.values.tolist(),
            "selected_liquid_level_fraction": self.selected_liquid_level_fraction.values.tolist(),
            "selected_ice_level_fraction": self.selected_ice_level_fraction.values.tolist(),
            "selected_mixed_level_fraction": self.selected_mixed_level_fraction.values.tolist(),
            "selected_risk_level_fraction": self.selected_risk_level_fraction.values.tolist(),
            "time_liquid_level_fraction": self.time_liquid_level_fraction.values.tolist(),
            "time_ice_level_fraction": self.time_ice_level_fraction.values.tolist(),
            "time_mixed_level_fraction": self.time_mixed_level_fraction.values.tolist(),
            "time_risk_level_fraction": self.time_risk_level_fraction.values.tolist(),
            "time_liquid_horizontal_fraction": self.time_liquid_horizontal_fraction.values.tolist(),
            "time_mixed_horizontal_fraction": self.time_mixed_horizontal_fraction.values.tolist(),
            "time_risk_horizontal_fraction": self.time_risk_horizontal_fraction.values.tolist(),
            "time_active_level_fraction": self.time_active_level_fraction.values.tolist(),
            "time_persistence_fraction": self.time_persistence_fraction.values.tolist(),
            "severity_score_time": self.severity_score_time.values.tolist(),
            "severity_class_time": list(self.severity_class_time),
            "severity_score": self.severity_score,
            "severity_class": self.severity_class,
            "persistence_fraction": self.persistence_fraction,
            "selected_active_level_ranges": list(self.selected_active_level_ranges),
            "band_summaries": [asdict(band) for band in self.band_summaries],
            "dominant_band": self.dominant_band,
            "heuristic_notes": list(self.heuristic_notes),
        }
        if output_paths is not None:
            payload["outputs"] = {name: str(path) for name, path in output_paths.items()}
        return payload

    def to_markdown(
        self,
        output_paths: dict[str, Path] | None = None,
        *,
        phase_number: int = 4,
    ) -> str:
        def _table(headers: list[str], rows: list[list[str]]) -> str:
            if not rows:
                rows = [["none" for _ in headers]]
            lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
            for row in rows:
                lines.append("| " + " | ".join(row) + " |")
            return "\n".join(lines)

        time_labels = [
            _coerce_time_value(value) or str(index)
            for index, value in enumerate(self.time_risk_horizontal_fraction.coords["Time"].values)
        ]
        band_rows = [
            [
                band.name,
                f"{band.eta_min:.2f} -> {band.eta_max:.2f}",
                str(band.level_count),
                str(band.active_level_count),
                f"{band.selected_risk_fraction:.1%}",
                f"{band.selected_liquid_fraction:.1%}",
                f"{band.selected_mixed_fraction:.1%}",
                f"{band.mean_risk_fraction:.1%}",
            ]
            for band in self.band_summaries
        ]
        time_rows = [
            [
                str(index),
                time_labels[index],
                self.severity_class_time[index],
                f"{float(score):.1f}",
                f"{float(risk):.1%}",
                f"{float(active):.1%}",
            ]
            for index, (score, risk, active) in enumerate(
                zip(
                    self.severity_score_time.values.tolist(),
                    self.time_risk_horizontal_fraction.values.tolist(),
                    self.time_active_level_fraction.values.tolist(),
                )
            )
        ]

        lines = [
            f"# Fase {phase_number}: severidad heuristica y rangos relativos del modelo",
            "",
            f"- Dataset: `{self.dataset_path}`",
            "- Product kind: heuristic proxy",
            f"- Time index: {self.time_index}",
            f"- Time label: {self.time_label or 'unknown'}",
            f"- Horizontal grid: {self.horizontal_shape[0]} x {self.horizontal_shape[1]}",
            f"- Vertical levels: {self.vertical_levels}",
            f"- Severity class: {self.severity_class} ({self.severity_score:.1f}/100)",
            f"- Dominant relative band: {self.dominant_band}",
            f"- Selected-time cumulative persistence: {self.time_persistence_fraction.values[self.time_index]:.1%}",
            f"- Selected-time approximate-risk cells: {self.time_risk_horizontal_fraction.values[self.time_index]:.1%}",
            f"- Selected-time liquid cells: {self.time_liquid_horizontal_fraction.values[self.time_index]:.1%}",
            f"- Selected-time mixed-phase cells: {self.time_mixed_horizontal_fraction.values[self.time_index]:.1%}",
            f"- Selected-time active relative levels: {self.time_active_level_fraction.values[self.time_index]:.1%}",
            "",
            "## Selected-time active ranges",
        ]
        if self.selected_active_level_ranges:
            lines.extend(f"- {item}" for item in self.selected_active_level_ranges)
        else:
            lines.append("- none")
        lines.extend(["", "## Relative bands", _table(
            ["Band", "eta range", "levels", "active", "risk", "liquid", "mixed", "mean risk"],
            band_rows,
        )])
        lines.extend(["", "## Temporal severity", _table(
            ["Time", "Label", "Class", "Score", "Risk", "Active levels"],
            time_rows,
        )])
        lines.extend(["", "## Heuristic notes"])
        lines.extend(f"- {note}" for note in self.heuristic_notes)
        if output_paths:
            lines.extend(["", "## Outputs"])
            lines.extend(f"- {name}: `{path}`" for name, path in output_paths.items())
        return "\n".join(lines)


Phase6HeuristicSeverityProduct = Phase4HeuristicSeverityProduct


def _coerce_time_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, np.ndarray):
        if value.size == 0:
            return None
        if value.shape == ():
            return _coerce_time_value(value.item())
        return _coerce_time_value(value.flat[0])
    if isinstance(value, np.datetime64):
        return np.datetime_as_string(value, unit="s")
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")
    if isinstance(value, np.generic):
        return _coerce_time_value(value.item())
    text = str(value).strip()
    return text or None


def _canonical_time_index(dataset: xr.Dataset, time_index: int) -> int:
    if "Time" not in dataset.sizes:
        raise ValueError("Dataset does not contain a Time dimension.")
    time_count = int(dataset.sizes["Time"])
    if time_count == 0:
        raise ValueError("Dataset contains no time steps.")
    if time_index < 0:
        time_index = time_count + time_index
    if time_index < 0 or time_index >= time_count:
        raise ValueError(f"time_index {time_index} is outside the available range 0..{time_count - 1}.")
    return time_index


def _selected_time_label(selected: xr.Dataset) -> str | None:
    if "XTIME" not in selected:
        return None
    return _coerce_time_value(selected["XTIME"].values)


def _reference_slice(dataset: xr.Dataset) -> xr.Dataset:
    if "Time" not in dataset.sizes:
        return dataset
    return dataset.isel(Time=0)


def _eta_mid(dataset: xr.Dataset) -> xr.DataArray:
    reference = _reference_slice(dataset)
    if "ZNW" not in reference:
        raise ValueError("Cannot derive heuristic severity without ZNW.")
    znw = reference["ZNW"]
    if "bottom_top_stag" not in znw.dims:
        raise ValueError("ZNW must include a bottom_top_stag dimension.")
    if znw.sizes["bottom_top_stag"] < 2:
        raise ValueError("ZNW must contain at least two staggered levels.")
    eta_values = 0.5 * (
        znw.isel(bottom_top_stag=slice(0, -1)).values + znw.isel(bottom_top_stag=slice(1, None)).values
    )
    return xr.DataArray(eta_values.astype(np.float32), dims=("bottom_top",), name="eta_mid")


def _classify_severity(score: float) -> str:
    if score <= 0.0:
        return "none"
    if score < HEURISTIC_SEVERITY_SCORE_THRESHOLDS[0]:
        return "low"
    if score < HEURISTIC_SEVERITY_SCORE_THRESHOLDS[1]:
        return "moderate"
    if score < HEURISTIC_SEVERITY_SCORE_THRESHOLDS[2]:
        return "high"
    return "severe"


def _format_level_range(start_index: int, end_index: int, eta_mid: np.ndarray) -> str:
    return (
        f"bottom_top {start_index}-{end_index} "
        f"(eta {float(eta_mid[start_index]):.2f} -> {float(eta_mid[end_index]):.2f})"
    )


def _active_level_ranges(mask: np.ndarray, eta_mid: np.ndarray) -> tuple[str, ...]:
    ranges: list[str] = []
    start_index: int | None = None
    for index, is_active in enumerate(mask.tolist()):
        if is_active and start_index is None:
            start_index = index
        elif not is_active and start_index is not None:
            ranges.append(_format_level_range(start_index, index - 1, eta_mid))
            start_index = None
    if start_index is not None:
        ranges.append(_format_level_range(start_index, len(mask) - 1, eta_mid))
    return tuple(ranges)


def _band_summaries(
    selected_risk_level_fraction: xr.DataArray,
    selected_liquid_level_fraction: xr.DataArray,
    selected_mixed_level_fraction: xr.DataArray,
    time_risk_level_fraction: xr.DataArray,
    eta_mid: xr.DataArray,
) -> tuple[SeverityBandSummary, ...]:
    summaries: list[SeverityBandSummary] = []
    eta_values = eta_mid.values
    for name, eta_min, eta_max in HEURISTIC_VERTICAL_BANDS:
        if name == "upper":
            level_mask = eta_values >= eta_min
        else:
            level_mask = (eta_values >= eta_min) & (eta_values < eta_max)
        level_indices = np.flatnonzero(level_mask)
        if level_indices.size:
            selected_risk = float(selected_risk_level_fraction.values[level_indices].mean())
            selected_liquid = float(selected_liquid_level_fraction.values[level_indices].mean())
            selected_mixed = float(selected_mixed_level_fraction.values[level_indices].mean())
            mean_risk = float(time_risk_level_fraction.mean(dim="Time").values[level_indices].mean())
            active_count = int(np.count_nonzero(selected_risk_level_fraction.values[level_indices] >= HEURISTIC_LEVEL_ACTIVITY_THRESHOLD))
        else:
            selected_risk = selected_liquid = selected_mixed = mean_risk = 0.0
            active_count = 0
        summaries.append(
            SeverityBandSummary(
                name=name,
                eta_min=float(eta_min),
                eta_max=float(eta_max),
                level_count=int(level_indices.size),
                active_level_count=active_count,
                selected_risk_fraction=selected_risk,
                selected_liquid_fraction=selected_liquid,
                selected_mixed_fraction=selected_mixed,
                mean_risk_fraction=mean_risk,
            )
        )
    return tuple(summaries)


def _severity_score(
    risk_horizontal_fraction: xr.DataArray,
    liquid_horizontal_fraction: xr.DataArray,
    mixed_horizontal_fraction: xr.DataArray,
    active_level_fraction: xr.DataArray,
    persistence_fraction: xr.DataArray,
) -> xr.DataArray:
    score = (
        HEURISTIC_SEVERITY_WEIGHTS["risk_horizontal"] * risk_horizontal_fraction
        + HEURISTIC_SEVERITY_WEIGHTS["liquid_horizontal"] * liquid_horizontal_fraction
        + HEURISTIC_SEVERITY_WEIGHTS["mixed_horizontal"] * mixed_horizontal_fraction
        + HEURISTIC_SEVERITY_WEIGHTS["vertical_span"] * active_level_fraction
        + HEURISTIC_SEVERITY_WEIGHTS["persistence"] * persistence_fraction
    ) * 100.0
    return xr.where(risk_horizontal_fraction > 0, score, 0.0)


def _build_output_dataset(product: Phase4HeuristicSeverityProduct, *, phase_number: int = 4) -> xr.Dataset:
    band_coord = xr.DataArray([band.name for band in product.band_summaries], dims=("severity_band",))
    severity_class_index = xr.DataArray(
        np.asarray([{"none": 0, "low": 1, "moderate": 2, "high": 3, "severe": 4}[name] for name in product.severity_class_time], dtype=np.uint8),
        dims=("Time",),
        coords={"Time": product.time_liquid_horizontal_fraction.coords["Time"]},
        name="time_severity_class_index",
    )
    return xr.Dataset(
        data_vars={
            "selected_liquid_level_fraction": product.selected_liquid_level_fraction,
            "selected_ice_level_fraction": product.selected_ice_level_fraction,
            "selected_mixed_level_fraction": product.selected_mixed_level_fraction,
            "selected_risk_level_fraction": product.selected_risk_level_fraction,
            "time_liquid_level_fraction": product.time_liquid_level_fraction,
            "time_ice_level_fraction": product.time_ice_level_fraction,
            "time_mixed_level_fraction": product.time_mixed_level_fraction,
            "time_risk_level_fraction": product.time_risk_level_fraction,
            "time_liquid_horizontal_fraction": product.time_liquid_horizontal_fraction,
            "time_mixed_horizontal_fraction": product.time_mixed_horizontal_fraction,
            "time_risk_horizontal_fraction": product.time_risk_horizontal_fraction,
            "time_active_level_fraction": product.time_active_level_fraction,
            "time_persistence_fraction": product.time_persistence_fraction,
            "time_severity_score": product.severity_score_time,
            "time_severity_class_index": severity_class_index,
            "band_selected_risk_fraction": xr.DataArray(
                np.asarray([band.selected_risk_fraction for band in product.band_summaries], dtype=np.float32),
                dims=("severity_band",),
                coords={"severity_band": band_coord},
            ),
            "band_selected_liquid_fraction": xr.DataArray(
                np.asarray([band.selected_liquid_fraction for band in product.band_summaries], dtype=np.float32),
                dims=("severity_band",),
                coords={"severity_band": band_coord},
            ),
            "band_selected_mixed_fraction": xr.DataArray(
                np.asarray([band.selected_mixed_fraction for band in product.band_summaries], dtype=np.float32),
                dims=("severity_band",),
                coords={"severity_band": band_coord},
            ),
            "band_mean_risk_fraction": xr.DataArray(
                np.asarray([band.mean_risk_fraction for band in product.band_summaries], dtype=np.float32),
                dims=("severity_band",),
                coords={"severity_band": band_coord},
            ),
            "band_eta_min": xr.DataArray(
                np.asarray([band.eta_min for band in product.band_summaries], dtype=np.float32),
                dims=("severity_band",),
                coords={"severity_band": band_coord},
            ),
            "band_eta_max": xr.DataArray(
                np.asarray([band.eta_max for band in product.band_summaries], dtype=np.float32),
                dims=("severity_band",),
                coords={"severity_band": band_coord},
            ),
            "band_level_count": xr.DataArray(
                np.asarray([band.level_count for band in product.band_summaries], dtype=np.uint16),
                dims=("severity_band",),
                coords={"severity_band": band_coord},
            ),
            "band_active_level_count": xr.DataArray(
                np.asarray([band.active_level_count for band in product.band_summaries], dtype=np.uint16),
                dims=("severity_band",),
                coords={"severity_band": band_coord},
            ),
        },
        coords={
            "Time": product.time_liquid_horizontal_fraction.coords["Time"],
            "bottom_top": product.eta_mid.coords["bottom_top"],
            "eta_mid": product.eta_mid,
            "severity_band": band_coord,
        },
        attrs={
            "title": f"Phase {phase_number} heuristic severity diagnostic",
            "phase": phase_number,
            "product_kind": "heuristic proxy",
            "source_dataset": str(product.dataset_path),
            "time_index": product.time_index,
            "time_label": product.time_label or "unknown",
            "severity_definition": (
                "severity_score = 100 * (0.35*risk_horizontal + 0.20*liquid_horizontal + "
                "0.15*mixed_horizontal + 0.15*active_level_fraction + 0.15*cumulative_persistence_fraction)"
            ),
            "severity_thresholds": f"low<{HEURISTIC_SEVERITY_SCORE_THRESHOLDS[0]}, moderate<{HEURISTIC_SEVERITY_SCORE_THRESHOLDS[1]}, high<{HEURISTIC_SEVERITY_SCORE_THRESHOLDS[2]}, severe>={HEURISTIC_SEVERITY_SCORE_THRESHOLDS[2]}",
            "band_definition": "upper: eta_mid >= 0.66; middle: 0.33 <= eta_mid < 0.66; lower: eta_mid < 0.33",
            "approximation_notes": " | ".join(product.heuristic_notes),
            "selected_active_level_ranges": " | ".join(product.selected_active_level_ranges) if product.selected_active_level_ranges else "none",
            "dominant_band": product.dominant_band,
        },
    )


def _render_severity_figure(product: Phase4HeuristicSeverityProduct, output_path: Path, *, phase_number: int = 4) -> None:
    fig, axes = plt.subplots(3, 1, figsize=(12, 12), constrained_layout=True, gridspec_kw={"height_ratios": [2.2, 1.0, 1.0]})
    fig.suptitle(f"Phase {phase_number}: heuristic severity proxy")
    time_positions = np.arange(product.time_risk_level_fraction.sizes["Time"])
    time_labels = [_coerce_time_value(value) or str(index) for index, value in enumerate(product.time_risk_horizontal_fraction.coords["Time"].values)]

    heatmap = product.time_risk_level_fraction.transpose("bottom_top", "Time").values
    mesh = axes[0].pcolormesh(time_positions, product.eta_mid.values, heatmap, shading="auto", cmap="magma", vmin=0.0, vmax=1.0)
    axes[0].axvline(product.time_index, color="#22c55e", linestyle="--", linewidth=1.5)
    axes[0].set_title("Approximate risk by model level and time")
    axes[0].set_ylabel("eta_mid")
    axes[0].set_xlabel("Time step")
    axes[0].set_xticks(time_positions)
    axes[0].set_xticklabels(time_labels, rotation=45, ha="right")
    fig.colorbar(mesh, ax=axes[0], fraction=0.046, pad=0.04, label="risk fraction")

    band_names = [band.name for band in product.band_summaries]
    band_values = [band.selected_risk_fraction for band in product.band_summaries]
    axes[1].bar(band_names, band_values, color=["#2563eb", "#f59e0b", "#b91c1c"])
    axes[1].set_ylim(0.0, 1.0)
    axes[1].set_title("Selected-time relative bands")
    axes[1].set_ylabel("risk fraction")
    for band, value in zip(product.band_summaries, band_values):
        axes[1].text(band.name, min(value + 0.03, 0.98), f"{value:.1%}", ha="center", va="bottom", fontsize=9)

    score_values = product.severity_score_time.values
    axes[2].plot(time_positions, score_values, color="#111827", marker="o", linewidth=1.5)
    for threshold in HEURISTIC_SEVERITY_SCORE_THRESHOLDS:
        axes[2].axhline(threshold, color="#9ca3af", linestyle=":", linewidth=1.0)
    axes[2].axvline(product.time_index, color="#22c55e", linestyle="--", linewidth=1.5)
    axes[2].set_ylim(0.0, 100.0)
    axes[2].set_title("Heuristic severity score across the series")
    axes[2].set_ylabel("score")
    axes[2].set_xlabel("Time step")
    axes[2].set_xticks(time_positions)
    axes[2].set_xticklabels(time_labels, rotation=45, ha="right")
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def build_phase4_heuristic_severity_product(
    dataset: xr.Dataset,
    dataset_path: str | Path,
    time_index: int = 0,
) -> Phase4HeuristicSeverityProduct:
    required_variables = ("QCLOUD", "QRAIN", "QICE", "T", "P", "ZNW")
    missing_variables = [name for name in required_variables if name not in dataset]
    if missing_variables:
        raise ValueError(f"Cannot derive heuristic severity without: {', '.join(missing_variables)}")

    selected_time_index = _canonical_time_index(dataset, time_index)
    selected = dataset.isel(Time=selected_time_index)
    selected_phase5 = build_phase5_approximate_risk_product(dataset, dataset_path, time_index=selected_time_index)

    eta_mid = _eta_mid(dataset)
    time_coord = dataset["XTIME"] if "XTIME" in dataset else xr.DataArray(np.arange(dataset.sizes["Time"]), dims=("Time",))
    pressure_base = (
        APPROXIMATE_PRESSURE_TOP_PA
        + eta_mid * (APPROXIMATE_PRESSURE_SURFACE_PA - APPROXIMATE_PRESSURE_TOP_PA)
    ).broadcast_like(dataset["P"])
    theta = (dataset["T"] + CORE_T0_K).astype(np.float32)
    pressure_proxy = (dataset["P"] + pressure_base).astype(np.float32)
    temperature_proxy = (theta * (pressure_proxy / 100000.0) ** APPROXIMATE_POISSON_KAPPA).astype(np.float32)

    liquid_3d = (dataset["QCLOUD"].fillna(0) + dataset["QRAIN"].fillna(0)) > 0
    ice_3d = dataset["QICE"].fillna(0) > 0
    mixed_3d = liquid_3d & ice_3d
    risk_3d = liquid_3d & (temperature_proxy <= APPROXIMATE_FREEZING_THRESHOLD_K)

    selected_liquid_level_fraction = liquid_3d.isel(Time=selected_time_index).mean(dim=("south_north", "west_east")).astype(np.float32)
    selected_ice_level_fraction = ice_3d.isel(Time=selected_time_index).mean(dim=("south_north", "west_east")).astype(np.float32)
    selected_mixed_level_fraction = mixed_3d.isel(Time=selected_time_index).mean(dim=("south_north", "west_east")).astype(np.float32)
    selected_risk_level_fraction = risk_3d.isel(Time=selected_time_index).mean(dim=("south_north", "west_east")).astype(np.float32)

    time_liquid_level_fraction = liquid_3d.mean(dim=("south_north", "west_east")).astype(np.float32).assign_coords(Time=time_coord)
    time_ice_level_fraction = ice_3d.mean(dim=("south_north", "west_east")).astype(np.float32).assign_coords(Time=time_coord)
    time_mixed_level_fraction = mixed_3d.mean(dim=("south_north", "west_east")).astype(np.float32).assign_coords(Time=time_coord)
    time_risk_level_fraction = risk_3d.mean(dim=("south_north", "west_east")).astype(np.float32).assign_coords(Time=time_coord)

    time_liquid_horizontal_fraction = (
        liquid_3d.any(dim="bottom_top").mean(dim=("south_north", "west_east")).astype(np.float32).assign_coords(Time=time_coord)
    )
    time_mixed_horizontal_fraction = (
        mixed_3d.any(dim="bottom_top").mean(dim=("south_north", "west_east")).astype(np.float32).assign_coords(Time=time_coord)
    )
    time_risk_horizontal_fraction = (
        risk_3d.any(dim="bottom_top").mean(dim=("south_north", "west_east")).astype(np.float32).assign_coords(Time=time_coord)
    )
    time_active_level_fraction = (
        (time_risk_level_fraction >= HEURISTIC_LEVEL_ACTIVITY_THRESHOLD).mean(dim="bottom_top").astype(np.float32).assign_coords(Time=time_coord)
    )

    # Persistence is accumulated only up to each time step so later future times
    # cannot retroactively change an earlier score.
    risk_active_time = (time_risk_horizontal_fraction > 0).astype(np.float32)
    cumulative_hits = risk_active_time.cumsum(dim="Time")
    time_indices = xr.DataArray(
        np.arange(1, risk_active_time.sizes["Time"] + 1, dtype=np.float32),
        dims=("Time",),
        coords={"Time": risk_active_time.coords["Time"]},
    )
    time_persistence_fraction = (cumulative_hits / time_indices).astype(np.float32)
    persistence_fraction = float(time_persistence_fraction.isel(Time=selected_time_index).item())
    severity_score_time = _severity_score(
        time_risk_horizontal_fraction,
        time_liquid_horizontal_fraction,
        time_mixed_horizontal_fraction,
        time_active_level_fraction,
        time_persistence_fraction,
    )
    severity_class_time = tuple(_classify_severity(float(score)) for score in severity_score_time.values.tolist())
    severity_score = float(severity_score_time.isel(Time=selected_time_index).item())
    severity_class = severity_class_time[selected_time_index]

    selected_active_level_ranges = _active_level_ranges(
        selected_risk_level_fraction.values >= HEURISTIC_LEVEL_ACTIVITY_THRESHOLD,
        eta_mid.values,
    )
    band_summaries = _band_summaries(
        selected_risk_level_fraction,
        selected_liquid_level_fraction,
        selected_mixed_level_fraction,
        time_risk_level_fraction,
        eta_mid,
    )
    dominant_band = "none"
    if severity_class != "none":
        dominant_band = max(
            band_summaries,
            key=lambda band: (band.selected_risk_fraction, band.selected_mixed_fraction, band.active_level_count),
        ).name

    heuristic_notes = (
        "severity is a heuristic proxy built on liquid fraction, mixed-phase context, vertical span and persistence.",
        f"risk_fraction levels are considered active when they reach at least {HEURISTIC_LEVEL_ACTIVITY_THRESHOLD:.2f} of the horizontal domain.",
        "persistence is cumulative up to each time step, so future times cannot revise earlier scores.",
        (
            f"severity thresholds are low<{HEURISTIC_SEVERITY_SCORE_THRESHOLDS[0]:.0f}, "
            f"moderate<{HEURISTIC_SEVERITY_SCORE_THRESHOLDS[1]:.0f}, "
            f"high<{HEURISTIC_SEVERITY_SCORE_THRESHOLDS[2]:.0f}, severe otherwise."
        ),
        "vertical bands are relative model-level groups: upper, middle and lower eta ranges.",
        (
            "the score is intentionally not an exact physical intensity metric because PB is unavailable."
            if "PB" not in dataset
            else "the score remains a heuristic proxy even when PB is present; PB-based thermodynamic refinement is still future work."
        ),
    )

    return Phase4HeuristicSeverityProduct(
        dataset_path=Path(dataset_path),
        time_index=selected_time_index,
        time_label=_selected_time_label(selected),
        horizontal_shape=(
            int(selected_phase5.liquid_presence.sizes.get("south_north", 0)),
            int(selected_phase5.liquid_presence.sizes.get("west_east", 0)),
        ),
        vertical_levels=int(dataset.sizes.get("bottom_top", 0)),
        eta_mid=eta_mid,
        selected_liquid_level_fraction=selected_liquid_level_fraction.assign_coords(eta_mid=eta_mid),
        selected_ice_level_fraction=selected_ice_level_fraction.assign_coords(eta_mid=eta_mid),
        selected_mixed_level_fraction=selected_mixed_level_fraction.assign_coords(eta_mid=eta_mid),
        selected_risk_level_fraction=selected_risk_level_fraction.assign_coords(eta_mid=eta_mid),
        time_liquid_level_fraction=time_liquid_level_fraction.assign_coords(eta_mid=eta_mid),
        time_ice_level_fraction=time_ice_level_fraction.assign_coords(eta_mid=eta_mid),
        time_mixed_level_fraction=time_mixed_level_fraction.assign_coords(eta_mid=eta_mid),
        time_risk_level_fraction=time_risk_level_fraction.assign_coords(eta_mid=eta_mid),
        time_liquid_horizontal_fraction=time_liquid_horizontal_fraction,
        time_mixed_horizontal_fraction=time_mixed_horizontal_fraction,
        time_risk_horizontal_fraction=time_risk_horizontal_fraction,
        time_active_level_fraction=time_active_level_fraction,
        time_persistence_fraction=time_persistence_fraction,
        severity_score_time=severity_score_time,
        severity_class_time=severity_class_time,
        severity_score=severity_score,
        severity_class=severity_class,
        persistence_fraction=persistence_fraction,
        selected_active_level_ranges=selected_active_level_ranges,
        band_summaries=band_summaries,
        dominant_band=dominant_band,
        heuristic_notes=heuristic_notes,
    )


def build_phase6_heuristic_severity_product(
    dataset: xr.Dataset,
    dataset_path: str | Path,
    time_index: int = 0,
) -> Phase6HeuristicSeverityProduct:
    return build_phase4_heuristic_severity_product(dataset, dataset_path, time_index=time_index)


def _write_heuristic_severity_outputs(
    product: Phase4HeuristicSeverityProduct,
    output_dir: str | Path,
    *,
    phase_number: int,
) -> tuple[Path, Path, Path, Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    base_name = f"phase{phase_number}_heuristic_severity_t{product.time_index:03d}"
    markdown_path = output_path / f"{base_name}.md"
    json_path = output_path / f"{base_name}.json"
    netcdf_path = output_path / f"{base_name}.nc"
    png_path = output_path / f"{base_name}.png"

    output_paths = {
        "markdown": markdown_path,
        "json": json_path,
        "netcdf": netcdf_path,
        "png": png_path,
    }

    _build_output_dataset(product, phase_number=phase_number).to_netcdf(netcdf_path)
    _render_severity_figure(product, png_path, phase_number=phase_number)
    markdown_path.write_text(product.to_markdown(output_paths, phase_number=phase_number), encoding="utf-8")
    json_path.write_text(
        json.dumps(product.to_dict(output_paths, phase_number=phase_number), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return markdown_path, json_path, netcdf_path, png_path


def write_phase4_outputs(
    product: Phase4HeuristicSeverityProduct,
    output_dir: str | Path,
) -> tuple[Path, Path, Path, Path]:
    return _write_heuristic_severity_outputs(product, output_dir, phase_number=4)


def write_phase6_outputs(
    product: Phase6HeuristicSeverityProduct,
    output_dir: str | Path,
) -> tuple[Path, Path, Path, Path]:
    return _write_heuristic_severity_outputs(product, output_dir, phase_number=6)
