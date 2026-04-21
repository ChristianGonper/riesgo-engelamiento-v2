from __future__ import annotations

import base64
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from .config import (
    FINAL_PRODUCT_VERTICAL_BAND_CHOICES,
    FINAL_PRODUCT_VERTICAL_BAND_MEANINGS,
)
from .phase4 import _coerce_time_value
from .phase6 import build_phase6_heuristic_severity_product
from .route_profile import build_route_icing_profile_product
from .severity_volume import build_severity_volume


@dataclass(frozen=True, slots=True)
class VerticalOption:
    id: str
    label: str
    kind: str
    eta_min: float | None
    eta_max: float | None
    level_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "kind": self.kind,
            "etaMin": self.eta_min,
            "etaMax": self.eta_max,
            "levelCount": self.level_count,
        }


def _canonical_time_index(dataset: xr.Dataset, time_index: int) -> int:
    time_count = int(dataset.sizes.get("Time", 0))
    if time_count <= 0:
        raise ValueError("Dataset contains no time steps.")
    if time_index < 0:
        time_index = time_count + time_index
    if time_index < 0 or time_index >= time_count:
        raise ValueError(
            f"timeIndex {time_index} is outside the available range 0..{time_count - 1}."
        )
    return time_index


def _selected_time_label(dataset: xr.Dataset, time_index: int) -> str | None:
    if "XTIME" not in dataset:
        return None
    return _coerce_time_value(dataset["XTIME"].isel(Time=time_index).values)


def _dataset_bounds(dataset: xr.Dataset) -> list[list[float]]:
    reference = dataset.isel(Time=0)
    lat = np.asarray(reference["XLAT"].values, dtype=np.float64)
    lon = np.asarray(reference["XLONG"].values, dtype=np.float64)
    return [
        [float(np.nanmin(lat)), float(np.nanmin(lon))],
        [float(np.nanmax(lat)), float(np.nanmax(lon))],
    ]


def _vertical_options(dataset: xr.Dataset) -> list[VerticalOption]:
    phase6 = build_phase6_heuristic_severity_product(dataset, "in-memory", time_index=0)
    by_name = {band.name: band for band in phase6.band_summaries}
    options: list[VerticalOption] = []
    for option_id in FINAL_PRODUCT_VERTICAL_BAND_CHOICES:
        if option_id == "dominant":
            options.append(
                VerticalOption(
                    id="dominant",
                    label="Franja dominante",
                    kind="band",
                    eta_min=None,
                    eta_max=None,
                    level_count=max(
                        (band.level_count for band in phase6.band_summaries), default=0
                    ),
                )
            )
            continue
        band = by_name[option_id]
        options.append(
            VerticalOption(
                id=option_id,
                label=FINAL_PRODUCT_VERTICAL_BAND_MEANINGS[option_id],
                kind="band",
                eta_min=float(band.eta_min),
                eta_max=float(band.eta_max),
                level_count=int(band.level_count),
            )
        )
    return options


def build_map_metadata(dataset: xr.Dataset, dataset_path: str | Path) -> dict[str, Any]:
    time_count = int(dataset.sizes.get("Time", 0))
    times = [
        {
            "index": index,
            "label": _selected_time_label(dataset, index) or f"t{index:03d}",
        }
        for index in range(time_count)
    ]
    return {
        "datasetPath": str(dataset_path),
        "timeCount": time_count,
        "times": times,
        "riskModes": [
            {"id": "generic", "label": "Perfil general"},
            {"id": "flight-level", "label": "Por capa vertical"},
        ],
        "verticalSelection": {
            "kind": "python-band",
            "label": "Franjas verticales derivadas del pipeline Python",
            "options": [option.to_dict() for option in _vertical_options(dataset)],
        },
        "mapBounds": _dataset_bounds(dataset),
    }


def _band_mask(option_id: str, phase6_product) -> np.ndarray:
    eta_mid = np.asarray(phase6_product.eta_mid.values, dtype=np.float32)
    if option_id == "dominant":
        option_id = phase6_product.dominant_band
    if option_id == "upper":
        return eta_mid >= 0.66
    if option_id == "middle":
        return (eta_mid >= 0.33) & (eta_mid < 0.66)
    if option_id == "lower":
        return eta_mid < 0.33
    raise ValueError(f"Unsupported vertical option: {option_id}")


def _severity_to_overlay_rgba(values: np.ndarray) -> np.ndarray:
    normalized = np.clip(values / 100.0, 0.0, 1.0)
    rgba = plt.get_cmap("magma")(normalized)
    alpha = np.where(values >= 1.0, np.clip(0.12 + normalized * 0.78, 0.0, 0.9), 0.0)
    rgba[..., 3] = alpha
    rgba[..., :3] = np.where(alpha[..., None] > 0.0, rgba[..., :3], 0.0)
    return rgba


def _array_to_png_data_url(values: np.ndarray) -> str:
    rgba = _severity_to_overlay_rgba(values)
    buffer = BytesIO()
    plt.imsave(buffer, rgba, format="png")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def build_risk_map_payload(
    dataset: xr.Dataset,
    dataset_path: str | Path,
    *,
    time_index: int,
    mode: str,
    vertical_option: str | None,
) -> dict[str, Any]:
    selected_time_index = _canonical_time_index(dataset, time_index)
    severity_3d, formula, source_metrics = build_severity_volume(
        dataset, dataset_path, time_index=selected_time_index
    )
    phase6 = build_phase6_heuristic_severity_product(
        dataset, dataset_path, time_index=selected_time_index
    )

    if mode == "generic":
        map_values = np.nanmax(np.asarray(severity_3d.values, dtype=np.float32), axis=0)
        resolved_vertical_option = None
    elif mode == "flight-level":
        option_id = vertical_option or "dominant"
        mask = _band_mask(option_id, phase6)
        if not np.any(mask):
            raise ValueError(f"Vertical option {option_id} resolved to an empty band.")
        map_values = np.nanmax(
            np.asarray(severity_3d.values, dtype=np.float32)[mask, :, :], axis=0
        )
        resolved_vertical_option = (
            option_id if option_id != "dominant" else phase6.dominant_band
        )
    else:
        raise ValueError(f"Unsupported risk mode: {mode}")

    selected = dataset.isel(Time=selected_time_index)
    lat = np.asarray(selected["XLAT"].values, dtype=np.float32)
    lon = np.asarray(selected["XLONG"].values, dtype=np.float32)
    return {
        "timeIndex": selected_time_index,
        "timeLabel": _selected_time_label(dataset, selected_time_index),
        "mode": mode,
        "verticalOption": vertical_option,
        "resolvedVerticalOption": resolved_vertical_option,
        "bounds": _dataset_bounds(dataset),
        "gridShape": [int(map_values.shape[0]), int(map_values.shape[1])],
        "severityRange": [float(np.nanmin(map_values)), float(np.nanmax(map_values))],
        "overlayImage": _array_to_png_data_url(map_values),
        "latitudes": lat[:, 0].tolist(),
        "longitudes": lon[0, :].tolist(),
        "severityFormula": formula,
        "sourceMetrics": source_metrics,
    }


def build_cross_section_payload(
    dataset: xr.Dataset,
    dataset_path: str | Path,
    *,
    time_index: int,
    route_start_lat: float,
    route_start_lon: float,
    route_end_lat: float,
    route_end_lon: float,
    route_points: int,
) -> dict[str, Any]:
    product = build_route_icing_profile_product(
        dataset,
        dataset_path,
        time_index=time_index,
        route_start_lat=route_start_lat,
        route_start_lon=route_start_lon,
        route_end_lat=route_end_lat,
        route_end_lon=route_end_lon,
        route_points=route_points,
    )
    return {
        **product.to_dict(),
        "xAxisLabel": "Distancia acumulada (km)",
        "yAxisLabel": "eta_mid (nivel relativo)",
        "verticalExtent": "surface-to-maximum",
        "visualBands": [
            {"label": "Bajo", "start": 0.0, "end": 0.33},
            {"label": "Medio", "start": 0.33, "end": 0.66},
            {"label": "Alto", "start": 0.66, "end": 1.0},
        ],
    }


__all__ = [
    "build_cross_section_payload",
    "build_map_metadata",
    "build_risk_map_payload",
]
