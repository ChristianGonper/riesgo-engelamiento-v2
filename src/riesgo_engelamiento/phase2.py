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

matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt  # noqa: E402

LIQUID_SOURCE_VARIABLES = ("QCLOUD", "QRAIN")


@dataclass(frozen=True, slots=True)
class Phase2LiquidProduct:
    dataset_path: Path
    time_index: int
    time_label: str | None
    horizontal_shape: tuple[int, int]
    vertical_levels: int
    liquid_amount: xr.DataArray
    liquid_presence: xr.DataArray
    liquid_cell_count: int
    empty_cell_count: int
    total_cell_count: int
    liquid_fraction: float
    has_liquid: bool

    def to_dict(self, output_paths: dict[str, Path] | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "dataset_path": str(self.dataset_path),
            "time_index": self.time_index,
            "time_label": self.time_label,
            "horizontal_shape": list(self.horizontal_shape),
            "vertical_levels": self.vertical_levels,
            "liquid_sources": list(LIQUID_SOURCE_VARIABLES),
            "binary_definition": "liquid_presence = any(bottom_top, QCLOUD + QRAIN > 0)",
            "liquid_cell_count": self.liquid_cell_count,
            "empty_cell_count": self.empty_cell_count,
            "total_cell_count": self.total_cell_count,
            "liquid_fraction": self.liquid_fraction,
            "has_liquid": self.has_liquid,
        }
        if output_paths is not None:
            payload["outputs"] = {name: str(path) for name, path in output_paths.items()}
        return payload

    def to_markdown(self, output_paths: dict[str, Path] | None = None) -> str:
        liquid_status = "present" if self.has_liquid else "absent"
        lines = [
            "# Fase 2: diagnostico binario de hidrometeoros liquidos",
            "",
            f"- Dataset: `{self.dataset_path}`",
            f"- Time index: {self.time_index}",
            f"- Time label: {self.time_label or 'unknown'}",
            f"- Horizontal grid: {self.horizontal_shape[0]} x {self.horizontal_shape[1]}",
            f"- Vertical levels scanned: {self.vertical_levels}",
            f"- Liquid sources: {', '.join(LIQUID_SOURCE_VARIABLES)}",
            f"- Binary definition: `any(bottom_top, QCLOUD + QRAIN > 0)`",
            f"- Liquid cells: {self.liquid_cell_count} / {self.total_cell_count} ({self.liquid_fraction:.1%})",
            f"- Empty cells: {self.empty_cell_count} / {self.total_cell_count}",
            f"- Liquid hydrometeors in selected time: {liquid_status}",
        ]
        if not self.has_liquid:
            lines.append("- No liquid hydrometeors were detected for the selected time step.")
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


def build_phase2_liquid_product(
    dataset: xr.Dataset,
    dataset_path: str | Path,
    time_index: int = 0,
) -> Phase2LiquidProduct:
    selected_time_index = _canonical_time_index(dataset, time_index)
    selected = dataset.isel(Time=selected_time_index)

    if "QCLOUD" not in selected or "QRAIN" not in selected:
        missing = [name for name in LIQUID_SOURCE_VARIABLES if name not in selected]
        raise ValueError(f"Cannot derive liquid presence without: {', '.join(missing)}")

    liquid_amount_3d = selected["QCLOUD"].fillna(0) + selected["QRAIN"].fillna(0)
    if "bottom_top" not in liquid_amount_3d.dims:
        raise ValueError("QCLOUD and QRAIN must include a bottom_top dimension.")

    liquid_presence_3d = liquid_amount_3d > 0
    liquid_amount = liquid_amount_3d.sum(dim="bottom_top")
    liquid_presence = liquid_presence_3d.any(dim="bottom_top")

    if "XLAT" in selected:
        liquid_amount = liquid_amount.assign_coords(XLAT=selected["XLAT"])
        liquid_presence = liquid_presence.assign_coords(XLAT=selected["XLAT"])
    if "XLONG" in selected:
        liquid_amount = liquid_amount.assign_coords(XLONG=selected["XLONG"])
        liquid_presence = liquid_presence.assign_coords(XLONG=selected["XLONG"])
    if "XTIME" in selected:
        liquid_amount = liquid_amount.assign_coords(XTIME=selected["XTIME"])
        liquid_presence = liquid_presence.assign_coords(XTIME=selected["XTIME"])

    total_cell_count = int(liquid_presence.size)
    liquid_cell_count = int(np.count_nonzero(liquid_presence.values))
    empty_cell_count = total_cell_count - liquid_cell_count
    liquid_fraction = float(liquid_cell_count / total_cell_count) if total_cell_count else 0.0

    return Phase2LiquidProduct(
        dataset_path=Path(dataset_path),
        time_index=selected_time_index,
        time_label=_selected_time_label(selected),
        horizontal_shape=(
            int(liquid_presence.sizes.get("south_north", 0)),
            int(liquid_presence.sizes.get("west_east", 0)),
        ),
        vertical_levels=int(dataset.sizes.get("bottom_top", 0)),
        liquid_amount=liquid_amount,
        liquid_presence=liquid_presence,
        liquid_cell_count=liquid_cell_count,
        empty_cell_count=empty_cell_count,
        total_cell_count=total_cell_count,
        liquid_fraction=liquid_fraction,
        has_liquid=liquid_cell_count > 0,
    )


def _build_output_dataset(product: Phase2LiquidProduct) -> xr.Dataset:
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
    return xr.Dataset(
        data_vars={
            "liquid_amount": liquid_amount,
            "liquid_presence": liquid_presence,
        },
        attrs={
            "title": "Phase 2 liquid hydrometeor diagnostic",
            "source_dataset": str(product.dataset_path),
            "time_index": product.time_index,
            "time_label": product.time_label or "unknown",
            "binary_definition": "liquid_presence = any(bottom_top, QCLOUD + QRAIN > 0)",
        },
    )


def _render_liquid_mask(product: Phase2LiquidProduct, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 6), constrained_layout=True)
    mask = product.liquid_presence.astype(np.uint8).values
    cmap = ListedColormap(["#f8fafc", "#2563eb"])
    if "XLAT" in product.liquid_presence.coords and "XLONG" in product.liquid_presence.coords:
        lon = product.liquid_presence.coords["XLONG"].values
        lat = product.liquid_presence.coords["XLAT"].values
        mesh = ax.pcolormesh(lon, lat, mask, shading="auto", cmap=cmap, vmin=0, vmax=1)
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
    else:
        mesh = ax.imshow(mask, origin="lower", cmap=cmap, vmin=0, vmax=1)
        ax.set_xlabel("west_east")
        ax.set_ylabel("south_north")
    ax.set_title(
        f"Liquid-water presence, time {product.time_index}"
        + (f" ({product.time_label})" if product.time_label else "")
    )
    cbar = fig.colorbar(mesh, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_ticks([0, 1])
    cbar.set_ticklabels(["absent", "present"])
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def write_phase2_outputs(
    product: Phase2LiquidProduct,
    output_dir: str | Path,
) -> tuple[Path, Path, Path, Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    base_name = f"phase2_liquid_presence_t{product.time_index:03d}"
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
    _render_liquid_mask(product, png_path)
    markdown_path.write_text(product.to_markdown(output_paths), encoding="utf-8")
    json_path.write_text(json.dumps(product.to_dict(output_paths), indent=2, ensure_ascii=False), encoding="utf-8")

    return markdown_path, json_path, netcdf_path, png_path
