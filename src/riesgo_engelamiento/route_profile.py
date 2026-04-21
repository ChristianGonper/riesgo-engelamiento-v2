from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import xarray as xr

from .config import (
    ROUTE_PROFILE_OUTPUT_PREFIX,
    ROUTE_PROFILE_OUTPUT_PURPOSE,
    ROUTE_PROFILE_REQUIRED_METADATA_FIELDS,
)
from .severity_volume import build_severity_volume

matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt  # noqa: E402


EARTH_RADIUS_KM = 6371.0


@dataclass(frozen=True, slots=True)
class RouteIcingProfileContract:
    artifact_kind: str = ROUTE_PROFILE_OUTPUT_PURPOSE
    output_prefix: str = ROUTE_PROFILE_OUTPUT_PREFIX
    required_metadata_fields: tuple[str, ...] = ROUTE_PROFILE_REQUIRED_METADATA_FIELDS

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_kind": self.artifact_kind,
            "output_prefix": self.output_prefix,
            "required_metadata_fields": list(self.required_metadata_fields),
        }


@dataclass(frozen=True, slots=True)
class RouteIcingProfileProduct:
    dataset_path: Path
    time_index: int
    time_label: str | None
    route_start: tuple[float, float]
    route_end: tuple[float, float]
    route_point_count: int
    route_lat: np.ndarray
    route_lon: np.ndarray
    distance_km: np.ndarray
    eta_mid: np.ndarray
    profile: np.ndarray
    severity_formula: str
    source_metrics: dict[str, Any]
    contract: RouteIcingProfileContract = field(
        default_factory=RouteIcingProfileContract
    )

    def to_dict(self, output_paths: dict[str, Path] | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "artifact_kind": self.contract.artifact_kind,
            "output_purpose": self.contract.artifact_kind,
            "dataset_path": str(self.dataset_path),
            "selected_time_index": self.time_index,
            "selected_time_label": self.time_label,
            "route_start": [float(self.route_start[0]), float(self.route_start[1])],
            "route_end": [float(self.route_end[0]), float(self.route_end[1])],
            "route_point_count": int(self.route_point_count),
            "distance_km_total": float(self.distance_km[-1])
            if self.distance_km.size
            else 0.0,
            "distance_km": self.distance_km.tolist(),
            "route_lat": self.route_lat.tolist(),
            "route_lon": self.route_lon.tolist(),
            "vertical_levels": int(self.eta_mid.size),
            "eta_mid": self.eta_mid.tolist(),
            "profile_shape": [int(self.profile.shape[0]), int(self.profile.shape[1])],
            "profile": self.profile.tolist(),
            "severity_range": [
                float(np.nanmin(self.profile)),
                float(np.nanmax(self.profile)),
            ],
            "severity_formula": self.severity_formula,
            "source_metrics": self.source_metrics,
            "contract": self.contract.to_dict(),
        }
        if output_paths is not None:
            payload["outputs"] = {
                name: str(path) for name, path in output_paths.items()
            }
        return payload

    def to_markdown(self, output_paths: dict[str, Path] | None = None) -> str:
        lines = [
            "# Perfil de engelamiento en ruta",
            "",
            f"- Artifact contract: `{self.contract.artifact_kind}`",
            f"- Dataset: `{self.dataset_path}`",
            f"- selected_time_index: {self.time_index}",
            f"- selected_time_label: {self.time_label or 'unknown'}",
            f"- Route start: ({self.route_start[0]:.5f}, {self.route_start[1]:.5f})",
            f"- Route end: ({self.route_end[0]:.5f}, {self.route_end[1]:.5f})",
            f"- Route points: {self.route_point_count}",
            f"- Route distance: {float(self.distance_km[-1]):.2f} km",
            f"- Vertical levels: {self.eta_mid.size}",
            f"- Profile shape (levels x distance): {self.profile.shape[0]} x {self.profile.shape[1]}",
            f"- Severity range: {float(np.nanmin(self.profile)):.2f} to {float(np.nanmax(self.profile)):.2f}",
            f"- Severity formula: {self.severity_formula}",
            "",
            "## Source metrics",
        ]
        for key, value in self.source_metrics.items():
            lines.append(f"- {key}: {value}")
        if output_paths:
            lines.extend(["", "## Outputs"])
            for key, path in output_paths.items():
                lines.append(f"- {key}: `{path}`")
        return "\n".join(lines)


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
        raise ValueError(
            f"time_index {time_index} is outside the available range 0..{time_count - 1}."
        )
    return time_index


def _selected_time_label(selected: xr.Dataset) -> str | None:
    if "XTIME" not in selected:
        return None
    return _coerce_time_value(selected["XTIME"].values)


def _validate_lat_lon(value: float, *, kind: str) -> float:
    value = float(value)
    if kind == "lat" and not (-90.0 <= value <= 90.0):
        raise ValueError(f"{kind} must be within [-90, 90], got {value}.")
    if kind == "lon" and not (-180.0 <= value <= 180.0):
        raise ValueError(f"{kind} must be within [-180, 180], got {value}.")
    return value


def _build_route_samples(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    point_count: int,
) -> tuple[np.ndarray, np.ndarray]:
    if point_count < 2:
        raise ValueError("route_points must be at least 2.")
    route_lat = np.linspace(start_lat, end_lat, point_count, dtype=np.float64)
    route_lon = np.linspace(start_lon, end_lon, point_count, dtype=np.float64)
    return route_lat, route_lon


def _haversine_km(
    lat1: np.ndarray, lon1: np.ndarray, lat2: np.ndarray, lon2: np.ndarray
) -> np.ndarray:
    lat1_rad = np.deg2rad(lat1)
    lon1_rad = np.deg2rad(lon1)
    lat2_rad = np.deg2rad(lat2)
    lon2_rad = np.deg2rad(lon2)
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
    return EARTH_RADIUS_KM * c


def _distance_axis_km(route_lat: np.ndarray, route_lon: np.ndarray) -> np.ndarray:
    if route_lat.size == 0:
        return np.asarray([], dtype=np.float64)
    segment = _haversine_km(
        route_lat[:-1], route_lon[:-1], route_lat[1:], route_lon[1:]
    )
    distance = np.zeros(route_lat.size, dtype=np.float64)
    if segment.size:
        distance[1:] = np.cumsum(segment)
    return distance


def _xy_to_index(
    lat_grid: np.ndarray, lon_grid: np.ndarray, lat: float, lon: float
) -> tuple[int, int]:
    delta = (lat_grid - lat) ** 2 + (lon_grid - lon) ** 2
    flat = int(np.argmin(delta))
    y_index, x_index = np.unravel_index(flat, delta.shape)
    return int(y_index), int(x_index)


def _route_profile_from_severity(
    severity_3d: xr.DataArray,
    lat_grid: np.ndarray,
    lon_grid: np.ndarray,
    route_lat: np.ndarray,
    route_lon: np.ndarray,
) -> np.ndarray:
    data = np.asarray(severity_3d.values, dtype=np.float32)
    levels = int(data.shape[0])
    points = int(route_lat.size)
    profile = np.zeros((levels, points), dtype=np.float32)
    for idx, (lat, lon) in enumerate(zip(route_lat, route_lon)):
        y_idx, x_idx = _xy_to_index(lat_grid, lon_grid, float(lat), float(lon))
        profile[:, idx] = data[:, y_idx, x_idx]
    return profile


def build_route_icing_profile_product(
    dataset: xr.Dataset,
    dataset_path: str | Path,
    *,
    time_index: int,
    route_start_lat: float,
    route_start_lon: float,
    route_end_lat: float,
    route_end_lon: float,
    route_points: int = 200,
) -> RouteIcingProfileProduct:
    selected_time_index = _canonical_time_index(dataset, int(time_index))
    selected = dataset.isel(Time=selected_time_index)
    start_lat = _validate_lat_lon(route_start_lat, kind="lat")
    start_lon = _validate_lat_lon(route_start_lon, kind="lon")
    end_lat = _validate_lat_lon(route_end_lat, kind="lat")
    end_lon = _validate_lat_lon(route_end_lon, kind="lon")

    if "XLAT" not in selected or "XLONG" not in selected:
        raise ValueError("Route profile requires XLAT and XLONG in the dataset.")
    lat_grid = np.asarray(selected["XLAT"].values, dtype=np.float64)
    lon_grid = np.asarray(selected["XLONG"].values, dtype=np.float64)
    lat_min = float(np.nanmin(lat_grid))
    lat_max = float(np.nanmax(lat_grid))
    lon_min = float(np.nanmin(lon_grid))
    lon_max = float(np.nanmax(lon_grid))
    if not (lat_min <= start_lat <= lat_max and lon_min <= start_lon <= lon_max):
        raise ValueError("Route start point is outside the dataset geographic domain.")
    if not (lat_min <= end_lat <= lat_max and lon_min <= end_lon <= lon_max):
        raise ValueError("Route end point is outside the dataset geographic domain.")
    route_lat, route_lon = _build_route_samples(
        start_lat, start_lon, end_lat, end_lon, int(route_points)
    )
    distance_km = _distance_axis_km(route_lat, route_lon)

    severity_3d, formula, source_metrics = build_severity_volume(
        dataset, dataset_path, time_index=selected_time_index
    )
    profile = _route_profile_from_severity(
        severity_3d, lat_grid, lon_grid, route_lat, route_lon
    )

    eta_mid_coord = severity_3d.coords.get("eta_mid")
    if eta_mid_coord is None:
        raise ValueError("Route profile requires eta_mid vertical coordinates.")
    eta_mid = np.asarray(eta_mid_coord.values, dtype=np.float32)

    source_metrics.update(
        {
            "domain_longitude_min": float(np.nanmin(lon_grid)),
            "domain_longitude_max": float(np.nanmax(lon_grid)),
            "domain_latitude_min": float(np.nanmin(lat_grid)),
            "domain_latitude_max": float(np.nanmax(lat_grid)),
            "profile_severity_mean": float(np.nanmean(profile)),
        }
    )

    return RouteIcingProfileProduct(
        dataset_path=Path(dataset_path),
        time_index=selected_time_index,
        time_label=_selected_time_label(selected),
        route_start=(start_lat, start_lon),
        route_end=(end_lat, end_lon),
        route_point_count=int(route_points),
        route_lat=route_lat.astype(np.float32),
        route_lon=route_lon.astype(np.float32),
        distance_km=distance_km.astype(np.float32),
        eta_mid=eta_mid,
        profile=profile,
        severity_formula=formula,
        source_metrics=source_metrics,
    )


def build_route_icing_profile_figure(product: RouteIcingProfileProduct):
    fig, ax = plt.subplots(figsize=(12.5, 5.8), constrained_layout=True)
    mesh = ax.pcolormesh(
        product.distance_km,
        product.eta_mid,
        product.profile,
        shading="auto",
        cmap="magma",
        vmin=0.0,
        vmax=100.0,
    )
    ax.set_title(
        "Perfil de severidad de engelamiento en ruta", loc="left", fontweight="bold"
    )
    subtitle = f"t={product.time_index:03d}" + (
        f" ({product.time_label})" if product.time_label else ""
    )
    ax.text(
        0.0, 1.02, subtitle, transform=ax.transAxes, ha="left", va="bottom", fontsize=10
    )
    ax.set_xlabel("Distancia acumulada (km)")
    ax.set_ylabel("eta_mid (nivel relativo)")
    ax.grid(True, linestyle="--", linewidth=0.6, alpha=0.28)
    cbar = fig.colorbar(mesh, ax=ax, fraction=0.046, pad=0.03)
    cbar.set_label("Severidad heuristica (0-100)")
    return fig


def _render_route_profile(product: RouteIcingProfileProduct, output_path: Path) -> None:
    fig = build_route_icing_profile_figure(product)
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def write_route_icing_profile_outputs(
    product: RouteIcingProfileProduct,
    output_dir: str | Path,
) -> tuple[Path, Path, Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    base_name = f"{product.contract.output_prefix}_t{product.time_index:03d}"
    markdown_path = output_path / f"{base_name}.md"
    json_path = output_path / f"{base_name}.json"
    png_path = output_path / f"{base_name}.png"
    output_paths = {
        "markdown": markdown_path,
        "json": json_path,
        "png": png_path,
    }

    _render_route_profile(product, png_path)
    markdown_path.write_text(product.to_markdown(output_paths), encoding="utf-8")
    json_path.write_text(
        json.dumps(product.to_dict(output_paths), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return markdown_path, json_path, png_path


__all__ = [
    "RouteIcingProfileContract",
    "RouteIcingProfileProduct",
    "build_route_icing_profile_product",
    "build_route_icing_profile_figure",
    "write_route_icing_profile_outputs",
]
