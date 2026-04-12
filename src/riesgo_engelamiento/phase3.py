from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import xarray as xr
from matplotlib.colors import ListedColormap

from .config import (
    APPROXIMATE_FREEZING_THRESHOLD_K,
    APPROXIMATE_POISSON_KAPPA,
    APPROXIMATE_PRESSURE_SURFACE_PA,
    APPROXIMATE_PRESSURE_TOP_PA,
    CORE_T0_K,
)
from .phase2 import LIQUID_SOURCE_VARIABLES

matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt  # noqa: E402


@dataclass(frozen=True, slots=True)
class Phase3ApproximateRiskProduct:
    dataset_path: Path
    time_index: int
    time_label: str | None
    horizontal_shape: tuple[int, int]
    vertical_levels: int
    theta: xr.DataArray
    pressure_proxy: xr.DataArray
    temperature_proxy: xr.DataArray
    temperature_c_proxy: xr.DataArray
    liquid_amount: xr.DataArray
    liquid_presence_3d: xr.DataArray
    liquid_presence: xr.DataArray
    risk_presence_3d: xr.DataArray
    risk_presence: xr.DataArray
    liquid_horizontal_cell_count: int
    liquid_vertical_cell_count: int
    risk_horizontal_cell_count: int
    risk_vertical_cell_count: int
    horizontal_cell_count: int
    vertical_cell_count: int
    liquid_horizontal_fraction: float
    liquid_vertical_fraction: float
    risk_horizontal_fraction: float
    risk_vertical_fraction: float
    theta_min_k: float
    theta_max_k: float
    pressure_proxy_min_pa: float
    pressure_proxy_max_pa: float
    temperature_proxy_min_k: float
    temperature_proxy_max_k: float
    temperature_proxy_min_c: float
    temperature_proxy_max_c: float
    has_liquid: bool
    has_risk: bool
    approximation_notes: tuple[str, ...]

    def to_dict(self, output_paths: dict[str, Path] | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "dataset_path": str(self.dataset_path),
            "time_index": self.time_index,
            "time_label": self.time_label,
            "horizontal_shape": list(self.horizontal_shape),
            "vertical_levels": self.vertical_levels,
            "liquid_sources": list(LIQUID_SOURCE_VARIABLES),
            "theta_definition": f"theta = T + {CORE_T0_K:.0f} K",
            "pressure_proxy_definition": (
                f"pressure_proxy = P + pressure_base, where pressure_base = {APPROXIMATE_PRESSURE_TOP_PA:.0f} Pa"
                f" + eta_mid * ({APPROXIMATE_PRESSURE_SURFACE_PA:.0f} - {APPROXIMATE_PRESSURE_TOP_PA:.0f}) Pa"
            ),
            "temperature_proxy_definition": (
                f"temperature_proxy = theta * (pressure_proxy / 100000 Pa) ** {APPROXIMATE_POISSON_KAPPA:.3f}"
            ),
            "risk_definition": (
                f"risk_presence_3d = liquid_presence_3d and temperature_proxy <= {APPROXIMATE_FREEZING_THRESHOLD_K:.2f} K"
            ),
            "liquid_horizontal_cell_count": self.liquid_horizontal_cell_count,
            "liquid_vertical_cell_count": self.liquid_vertical_cell_count,
            "risk_horizontal_cell_count": self.risk_horizontal_cell_count,
            "risk_vertical_cell_count": self.risk_vertical_cell_count,
            "horizontal_cell_count": self.horizontal_cell_count,
            "vertical_cell_count": self.vertical_cell_count,
            "liquid_horizontal_fraction": self.liquid_horizontal_fraction,
            "liquid_vertical_fraction": self.liquid_vertical_fraction,
            "risk_horizontal_fraction": self.risk_horizontal_fraction,
            "risk_vertical_fraction": self.risk_vertical_fraction,
            "theta_min_k": self.theta_min_k,
            "theta_max_k": self.theta_max_k,
            "pressure_proxy_min_pa": self.pressure_proxy_min_pa,
            "pressure_proxy_max_pa": self.pressure_proxy_max_pa,
            "temperature_proxy_min_k": self.temperature_proxy_min_k,
            "temperature_proxy_max_k": self.temperature_proxy_max_k,
            "temperature_proxy_min_c": self.temperature_proxy_min_c,
            "temperature_proxy_max_c": self.temperature_proxy_max_c,
            "has_liquid": self.has_liquid,
            "has_risk": self.has_risk,
            "approximation_notes": list(self.approximation_notes),
        }
        if output_paths is not None:
            payload["outputs"] = {name: str(path) for name, path in output_paths.items()}
        return payload

    def to_markdown(self, output_paths: dict[str, Path] | None = None) -> str:
        liquid_status = "present" if self.has_liquid else "absent"
        risk_status = "present" if self.has_risk else "absent"
        lines = [
            "# Fase 3: riesgo aproximado de engelamiento",
            "",
            f"- Dataset: `{self.dataset_path}`",
            f"- Time index: {self.time_index}",
            f"- Time label: {self.time_label or 'unknown'}",
            f"- Horizontal grid: {self.horizontal_shape[0]} x {self.horizontal_shape[1]}",
            f"- Vertical levels: {self.vertical_levels}",
            f"- Liquid sources: {', '.join(LIQUID_SOURCE_VARIABLES)}",
            f"- Theta definition: `theta = T + {CORE_T0_K:.0f} K`",
            (
                "- Pressure proxy: `pressure_proxy = P + pressure_base`, where `pressure_base = "
                f"{APPROXIMATE_PRESSURE_TOP_PA:.0f} Pa + eta_mid * ({APPROXIMATE_PRESSURE_SURFACE_PA:.0f} - "
                f"{APPROXIMATE_PRESSURE_TOP_PA:.0f}) Pa`"
            ),
            (
                "- Temperature proxy: `temperature_proxy = theta * (pressure_proxy / 100000 Pa) ** "
                f"{APPROXIMATE_POISSON_KAPPA:.3f}`"
            ),
            (
                "- Risk definition: `liquid_presence_3d and temperature_proxy <= "
                f"{APPROXIMATE_FREEZING_THRESHOLD_K:.2f} K`"
            ),
            f"- Theta range: {self.theta_min_k:.2f} K -> {self.theta_max_k:.2f} K",
            (
                f"- Pressure proxy range: {self.pressure_proxy_min_pa:.2f} Pa -> "
                f"{self.pressure_proxy_max_pa:.2f} Pa"
            ),
            (
                f"- Temperature proxy range: {self.temperature_proxy_min_k:.2f} K -> "
                f"{self.temperature_proxy_max_k:.2f} K"
            ),
            (
                f"- Temperature proxy range (C): {self.temperature_proxy_min_c:.2f} C -> "
                f"{self.temperature_proxy_max_c:.2f} C"
            ),
            f"- Liquid horizontal cells: {self.liquid_horizontal_cell_count} / {self.horizontal_cell_count} ({self.liquid_horizontal_fraction:.1%})",
            f"- Liquid vertical cells: {self.liquid_vertical_cell_count} / {self.vertical_cell_count} ({self.liquid_vertical_fraction:.1%})",
            f"- Approximate-risk horizontal cells: {self.risk_horizontal_cell_count} / {self.horizontal_cell_count} ({self.risk_horizontal_fraction:.1%})",
            f"- Approximate-risk vertical cells: {self.risk_vertical_cell_count} / {self.vertical_cell_count} ({self.risk_vertical_fraction:.1%})",
            f"- Liquid hydrometeors in selected time: {liquid_status}",
            f"- Approximate icing risk in selected time: {risk_status}",
        ]
        if not self.has_risk:
            lines.append("- No approximate icing risk was detected for the selected time step.")
        lines.extend(["", "## Approximation notes"])
        for note in self.approximation_notes:
            lines.append(f"- {note}")
        if output_paths:
            lines.extend(["", "## Outputs"])
            for name, path in output_paths.items():
                lines.append(f"- {name}: `{path}`")
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


def _eta_mid(selected: xr.Dataset) -> xr.DataArray:
    if "ZNW" not in selected:
        raise ValueError("Cannot derive approximate risk without ZNW.")
    znw = selected["ZNW"]
    if "bottom_top_stag" not in znw.dims:
        raise ValueError("ZNW must include a bottom_top_stag dimension.")
    if znw.sizes["bottom_top_stag"] < 2:
        raise ValueError("ZNW must contain at least two staggered levels.")
    eta_values = 0.5 * (
        znw.isel(bottom_top_stag=slice(0, -1)).values + znw.isel(bottom_top_stag=slice(1, None)).values
    )
    return xr.DataArray(eta_values.astype(np.float32), dims=("bottom_top",), name="eta_mid")


def _attach_horizontal_coords(field: xr.DataArray, selected: xr.Dataset) -> xr.DataArray:
    if "XLAT" in selected:
        field = field.assign_coords(XLAT=selected["XLAT"])
    if "XLONG" in selected:
        field = field.assign_coords(XLONG=selected["XLONG"])
    if "XTIME" in selected:
        field = field.assign_coords(XTIME=selected["XTIME"])
    return field


def _attach_vertical_coords(field: xr.DataArray, selected: xr.Dataset, eta_mid: xr.DataArray) -> xr.DataArray:
    field = field.assign_coords(eta_mid=eta_mid)
    if "XTIME" in selected:
        field = field.assign_coords(XTIME=selected["XTIME"])
    return field


def _build_liquid_fields(selected: xr.Dataset) -> tuple[xr.DataArray, xr.DataArray]:
    missing = [name for name in LIQUID_SOURCE_VARIABLES if name not in selected]
    if missing:
        raise ValueError(f"Cannot derive liquid presence without: {', '.join(missing)}")
    liquid_amount_3d = selected["QCLOUD"].fillna(0) + selected["QRAIN"].fillna(0)
    if "bottom_top" not in liquid_amount_3d.dims:
        raise ValueError("QCLOUD and QRAIN must include a bottom_top dimension.")
    liquid_presence_3d = liquid_amount_3d > 0
    return liquid_amount_3d, liquid_presence_3d


def _build_pressure_proxy(selected: xr.Dataset) -> tuple[xr.DataArray, xr.DataArray]:
    if "P" not in selected:
        raise ValueError("Cannot derive approximate risk without P.")
    eta_mid = _eta_mid(selected)
    base_profile = APPROXIMATE_PRESSURE_TOP_PA + eta_mid * (APPROXIMATE_PRESSURE_SURFACE_PA - APPROXIMATE_PRESSURE_TOP_PA)
    pressure_base = base_profile.broadcast_like(selected["P"])
    pressure_proxy = (pressure_base + selected["P"]).astype(np.float32)
    return eta_mid, pressure_proxy


def build_phase3_approximate_risk_product(
    dataset: xr.Dataset,
    dataset_path: str | Path,
    time_index: int = 0,
) -> Phase3ApproximateRiskProduct:
    selected_time_index = _canonical_time_index(dataset, time_index)
    selected = dataset.isel(Time=selected_time_index)

    liquid_amount_3d, liquid_presence_3d = _build_liquid_fields(selected)
    eta_mid, pressure_proxy = _build_pressure_proxy(selected)

    theta = (selected["T"] + CORE_T0_K).astype(np.float32)
    temperature_proxy = (theta * (pressure_proxy / 100000.0) ** APPROXIMATE_POISSON_KAPPA).astype(np.float32)
    temperature_c_proxy = (temperature_proxy - 273.15).astype(np.float32)

    liquid_presence_3d = liquid_presence_3d.astype(np.uint8)
    risk_presence_3d = (liquid_presence_3d.astype(bool) & (temperature_proxy <= APPROXIMATE_FREEZING_THRESHOLD_K)).astype(np.uint8)

    liquid_amount = liquid_amount_3d.sum(dim="bottom_top").astype(np.float32)
    liquid_presence = liquid_presence_3d.any(dim="bottom_top").astype(np.uint8)
    risk_presence = risk_presence_3d.any(dim="bottom_top").astype(np.uint8)

    theta = _attach_vertical_coords(theta, selected, eta_mid)
    pressure_proxy = _attach_vertical_coords(pressure_proxy, selected, eta_mid)
    temperature_proxy = _attach_vertical_coords(temperature_proxy, selected, eta_mid)
    temperature_c_proxy = _attach_vertical_coords(temperature_c_proxy, selected, eta_mid)
    liquid_presence_3d = _attach_vertical_coords(liquid_presence_3d, selected, eta_mid)
    risk_presence_3d = _attach_vertical_coords(risk_presence_3d, selected, eta_mid)
    liquid_amount = _attach_horizontal_coords(liquid_amount, selected)
    liquid_presence = _attach_horizontal_coords(liquid_presence, selected)
    risk_presence = _attach_horizontal_coords(risk_presence, selected)

    horizontal_cell_count = int(liquid_presence.size)
    vertical_cell_count = int(liquid_presence_3d.size)
    liquid_horizontal_cell_count = int(np.count_nonzero(liquid_presence.values))
    liquid_vertical_cell_count = int(np.count_nonzero(liquid_presence_3d.values))
    risk_horizontal_cell_count = int(np.count_nonzero(risk_presence.values))
    risk_vertical_cell_count = int(np.count_nonzero(risk_presence_3d.values))

    liquid_horizontal_fraction = float(liquid_horizontal_cell_count / horizontal_cell_count) if horizontal_cell_count else 0.0
    liquid_vertical_fraction = float(liquid_vertical_cell_count / vertical_cell_count) if vertical_cell_count else 0.0
    risk_horizontal_fraction = float(risk_horizontal_cell_count / horizontal_cell_count) if horizontal_cell_count else 0.0
    risk_vertical_fraction = float(risk_vertical_cell_count / vertical_cell_count) if vertical_cell_count else 0.0

    approximation_notes = (
        "theta is recovered as T + 300 K from the perturbation potential temperature field.",
        "pressure_proxy linearly interpolates between 5000 Pa at eta=0 and 100000 Pa at eta=1, then adds P.",
        f"temperature_proxy uses a Poisson exponent of {APPROXIMATE_POISSON_KAPPA:.3f} and a freezing threshold of {APPROXIMATE_FREEZING_THRESHOLD_K:.2f} K.",
        "risk is an explicit proxy and is not an exact thermodynamic diagnosis because PB is absent.",
    )

    return Phase3ApproximateRiskProduct(
        dataset_path=Path(dataset_path),
        time_index=selected_time_index,
        time_label=_selected_time_label(selected),
        horizontal_shape=(
            int(liquid_presence.sizes.get("south_north", 0)),
            int(liquid_presence.sizes.get("west_east", 0)),
        ),
        vertical_levels=int(dataset.sizes.get("bottom_top", 0)),
        theta=theta,
        pressure_proxy=pressure_proxy,
        temperature_proxy=temperature_proxy,
        temperature_c_proxy=temperature_c_proxy,
        liquid_amount=liquid_amount,
        liquid_presence_3d=liquid_presence_3d,
        liquid_presence=liquid_presence,
        risk_presence_3d=risk_presence_3d,
        risk_presence=risk_presence,
        liquid_horizontal_cell_count=liquid_horizontal_cell_count,
        liquid_vertical_cell_count=liquid_vertical_cell_count,
        risk_horizontal_cell_count=risk_horizontal_cell_count,
        risk_vertical_cell_count=risk_vertical_cell_count,
        horizontal_cell_count=horizontal_cell_count,
        vertical_cell_count=vertical_cell_count,
        liquid_horizontal_fraction=liquid_horizontal_fraction,
        liquid_vertical_fraction=liquid_vertical_fraction,
        risk_horizontal_fraction=risk_horizontal_fraction,
        risk_vertical_fraction=risk_vertical_fraction,
        theta_min_k=float(np.nanmin(theta.values)),
        theta_max_k=float(np.nanmax(theta.values)),
        pressure_proxy_min_pa=float(np.nanmin(pressure_proxy.values)),
        pressure_proxy_max_pa=float(np.nanmax(pressure_proxy.values)),
        temperature_proxy_min_k=float(np.nanmin(temperature_proxy.values)),
        temperature_proxy_max_k=float(np.nanmax(temperature_proxy.values)),
        temperature_proxy_min_c=float(np.nanmin(temperature_c_proxy.values)),
        temperature_proxy_max_c=float(np.nanmax(temperature_c_proxy.values)),
        has_liquid=liquid_horizontal_cell_count > 0,
        has_risk=risk_horizontal_cell_count > 0,
        approximation_notes=approximation_notes,
    )


def _build_output_dataset(product: Phase3ApproximateRiskProduct) -> xr.Dataset:
    theta = product.theta.copy()
    theta.attrs.update(
        {
            "description": "Total potential temperature reconstructed as T + 300 K.",
            "source_variable": "T",
        }
    )
    pressure_proxy = product.pressure_proxy.copy()
    pressure_proxy.attrs.update(
        {
            "description": "Approximate total pressure built from eta interpolation plus pressure perturbation P.",
            "source_variable": "P and ZNW",
        }
    )
    temperature_proxy = product.temperature_proxy.copy()
    temperature_proxy.attrs.update(
        {
            "description": "Approximate air temperature derived from theta and the pressure proxy.",
            "source_variables": "T, P, ZNW",
        }
    )
    temperature_c_proxy = product.temperature_c_proxy.copy()
    temperature_c_proxy.attrs.update(
        {
            "description": "Approximate air temperature derived from theta and the pressure proxy in Celsius.",
            "source_variables": "T, P, ZNW",
        }
    )
    liquid_presence_3d = product.liquid_presence_3d.astype(np.uint8).copy()
    liquid_presence_3d.attrs.update(
        {
            "description": "Binary 3D liquid mask derived from QCLOUD + QRAIN > 0.",
            "flag_values": "0, 1",
            "flag_meanings": "absent present",
        }
    )
    risk_presence_3d = product.risk_presence_3d.astype(np.uint8).copy()
    risk_presence_3d.attrs.update(
        {
            "description": "Binary 3D approximate icing-risk mask derived from liquid presence and subzero proxy temperature.",
            "flag_values": "0, 1",
            "flag_meanings": "absent present",
        }
    )
    liquid_amount = product.liquid_amount.copy()
    liquid_amount.attrs.update(
        {
            "description": "Horizontal liquid amount derived as the vertical sum of QCLOUD + QRAIN.",
            "source_variables": ", ".join(LIQUID_SOURCE_VARIABLES),
        }
    )
    liquid_presence = product.liquid_presence.astype(np.uint8).copy()
    liquid_presence.attrs.update(
        {
            "description": "Binary horizontal liquid mask derived from any(bottom_top, QCLOUD + QRAIN > 0).",
            "flag_values": "0, 1",
            "flag_meanings": "absent present",
        }
    )
    risk_presence = product.risk_presence.astype(np.uint8).copy()
    risk_presence.attrs.update(
        {
            "description": "Binary horizontal approximate icing-risk mask derived from any(bottom_top, risk_presence_3d > 0).",
            "flag_values": "0, 1",
            "flag_meanings": "absent present",
        }
    )

    return xr.Dataset(
        data_vars={
            "theta": theta,
            "pressure_proxy": pressure_proxy,
            "temperature_proxy": temperature_proxy,
            "temperature_c_proxy": temperature_c_proxy,
            "liquid_presence_3d": liquid_presence_3d,
            "risk_presence_3d": risk_presence_3d,
            "liquid_amount": liquid_amount,
            "liquid_presence": liquid_presence,
            "risk_presence": risk_presence,
        },
        coords={
            "eta_mid": product.theta.coords["eta_mid"],
        },
        attrs={
            "title": "Phase 3 approximate icing-risk diagnostic",
            "source_dataset": str(product.dataset_path),
            "time_index": product.time_index,
            "time_label": product.time_label or "unknown",
            "theta_definition": f"theta = T + {CORE_T0_K:.0f} K",
            "pressure_proxy_definition": (
                f"pressure_proxy = P + pressure_base, with pressure_base = {APPROXIMATE_PRESSURE_TOP_PA:.0f} Pa"
                f" + eta_mid * ({APPROXIMATE_PRESSURE_SURFACE_PA:.0f} - {APPROXIMATE_PRESSURE_TOP_PA:.0f}) Pa"
            ),
            "temperature_proxy_definition": (
                f"temperature_proxy = theta * (pressure_proxy / 100000 Pa) ** {APPROXIMATE_POISSON_KAPPA:.3f}"
            ),
            "risk_definition": (
                f"risk_presence_3d = liquid_presence_3d & (temperature_proxy <= {APPROXIMATE_FREEZING_THRESHOLD_K:.2f} K)"
            ),
            "approximation_notes": " | ".join(product.approximation_notes),
        },
    )


def _render_risk_mask(product: Phase3ApproximateRiskProduct, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 6), constrained_layout=True)
    mask = product.risk_presence.astype(np.uint8).values
    cmap = ListedColormap(["#f8fafc", "#b91c1c"])
    if "XLAT" in product.risk_presence.coords and "XLONG" in product.risk_presence.coords:
        lon = product.risk_presence.coords["XLONG"].values
        lat = product.risk_presence.coords["XLAT"].values
        mesh = ax.pcolormesh(lon, lat, mask, shading="auto", cmap=cmap, vmin=0, vmax=1)
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
    else:
        mesh = ax.imshow(mask, origin="lower", cmap=cmap, vmin=0, vmax=1)
        ax.set_xlabel("west_east")
        ax.set_ylabel("south_north")
    ax.set_title(
        f"Approximate icing risk, time {product.time_index}"
        + (f" ({product.time_label})" if product.time_label else "")
    )
    cbar = fig.colorbar(mesh, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_ticks([0, 1])
    cbar.set_ticklabels(["absent", "present"])
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def write_phase3_outputs(
    product: Phase3ApproximateRiskProduct,
    output_dir: str | Path,
) -> tuple[Path, Path, Path, Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    base_name = f"phase3_approximate_icing_risk_t{product.time_index:03d}"
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

    _build_output_dataset(product).to_netcdf(netcdf_path)
    _render_risk_mask(product, png_path)
    markdown_path.write_text(product.to_markdown(output_paths), encoding="utf-8")
    json_path.write_text(json.dumps(product.to_dict(output_paths), indent=2, ensure_ascii=False), encoding="utf-8")

    return markdown_path, json_path, netcdf_path, png_path
