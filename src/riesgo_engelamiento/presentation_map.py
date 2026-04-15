from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import matplotlib
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.colors import Normalize
from matplotlib.colors import ListedColormap
from matplotlib.patches import FancyBboxPatch
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator

matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt  # noqa: E402


@dataclass(frozen=True, slots=True)
class FinalProductMapStyle:
    figure_size: tuple[float, float] = (15.2, 8.6)
    dpi: int = 180
    figure_facecolor: str = "#f8fafc"
    map_facecolor: str = "#eef2f7"
    annotation_facecolor: str = "#ffffff"
    annotation_edgecolor: str = "#cbd5e1"
    title_color: str = "#0f172a"
    subtitle_color: str = "#334155"
    text_color: str = "#1e293b"
    muted_text_color: str = "#475569"
    grid_color: str = "#94a3b8"
    absent_color: str = "#eef2f7"
    present_color: str = "#b91c1c"
    present_edge_color: str = "#7f1d1d"
    legend_facecolor: str = "#ffffff"
    legend_edgecolor: str = "#cbd5e1"
    footer_color: str = "#475569"
    land_facecolor: str = "#f8fafc"
    ocean_facecolor: str = "#e2e8f0"
    coastline_color: str = "#334155"
    border_color: str = "#0f172a"
    info_box_alpha: float = 0.96

    def annotation_box(self) -> dict[str, Any]:
        return {
            "boxstyle": "round,pad=0.7",
            "facecolor": self.annotation_facecolor,
            "edgecolor": self.annotation_edgecolor,
            "linewidth": 1.0,
            "alpha": self.info_box_alpha,
        }


DEFAULT_FINAL_PRODUCT_MAP_STYLE = FinalProductMapStyle()


def create_final_product_canvas(
    style: FinalProductMapStyle = DEFAULT_FINAL_PRODUCT_MAP_STYLE,
) -> tuple[plt.Figure, plt.Axes, plt.Axes]:
    fig = plt.figure(figsize=style.figure_size, dpi=style.dpi, facecolor=style.figure_facecolor, constrained_layout=True)
    grid = fig.add_gridspec(1, 2, width_ratios=[4.6, 1.0])
    map_ax = fig.add_subplot(grid[0, 0], projection=ccrs.PlateCarree())
    annotation_ax = fig.add_subplot(grid[0, 1])
    map_ax.set_facecolor(style.map_facecolor)
    annotation_ax.set_facecolor(style.figure_facecolor)
    return fig, map_ax, annotation_ax


def _domain_extent(lon: np.ndarray, lat: np.ndarray, *, padding_fraction: float = 0.14, minimum_padding: float = 1.5) -> tuple[float, float, float, float]:
    lon_values = np.asarray(lon, dtype=np.float64)
    lat_values = np.asarray(lat, dtype=np.float64)
    lon_min = float(np.nanmin(lon_values))
    lon_max = float(np.nanmax(lon_values))
    lat_min = float(np.nanmin(lat_values))
    lat_max = float(np.nanmax(lat_values))

    lon_span = max(lon_max - lon_min, 0.5)
    lat_span = max(lat_max - lat_min, 0.5)
    lon_pad = max(lon_span * padding_fraction, minimum_padding)
    lat_pad = max(lat_span * padding_fraction, minimum_padding)
    return (
        lon_min - lon_pad,
        lon_max + lon_pad,
        lat_min - lat_pad,
        lat_max + lat_pad,
    )


def _add_geographic_context(
    ax: plt.Axes,
    *,
    lon: np.ndarray,
    lat: np.ndarray,
    style: FinalProductMapStyle = DEFAULT_FINAL_PRODUCT_MAP_STYLE,
) -> None:
    extent = _domain_extent(lon, lat)
    ax.set_extent(extent, crs=ccrs.PlateCarree())
    ax.add_feature(cfeature.LAND.with_scale("110m"), facecolor=style.land_facecolor, edgecolor="none", zorder=0)
    ax.add_feature(cfeature.OCEAN.with_scale("110m"), facecolor=style.ocean_facecolor, edgecolor="none", zorder=0)
    ax.add_feature(cfeature.COASTLINE.with_scale("110m"), edgecolor=style.coastline_color, linewidth=1.0, zorder=3)
    ax.add_feature(cfeature.BORDERS.with_scale("110m"), edgecolor=style.border_color, linewidth=1.1, zorder=3)
    gridlines = ax.gridlines(
        crs=ccrs.PlateCarree(),
        draw_labels=False,
        linewidth=0.6,
        color=style.grid_color,
        alpha=0.28,
        linestyle="--",
    )
    gridlines.xlocator = MaxNLocator(nbins=5)
    gridlines.ylocator = MaxNLocator(nbins=5)


def render_binary_geographic_map(
    ax: plt.Axes,
    field: np.ndarray,
    *,
    title: str,
    subtitle: str | None = None,
    lon: np.ndarray | None = None,
    lat: np.ndarray | None = None,
    legend_title: str = "Legend",
    legend_labels: tuple[str, str] = ("Absent", "Present"),
    style: FinalProductMapStyle = DEFAULT_FINAL_PRODUCT_MAP_STYLE,
) -> None:
    binary_field = np.asarray(field, dtype=np.uint8)
    cmap = ListedColormap([style.absent_color, style.present_color])
    if lon is not None and lat is not None:
        _add_geographic_context(ax, lon=lon, lat=lat, style=style)
        mesh = ax.pcolormesh(
            lon,
            lat,
            binary_field,
            shading="auto",
            cmap=cmap,
            vmin=0,
            vmax=1,
            transform=ccrs.PlateCarree(),
            zorder=1,
        )
        if np.any(binary_field > 0):
            ax.contour(
                lon,
                lat,
                binary_field,
                levels=[0.5],
                colors=style.present_edge_color,
                linewidths=1.25,
                transform=ccrs.PlateCarree(),
                zorder=2,
            )
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
        ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
    else:
        mesh = ax.imshow(binary_field, origin="lower", cmap=cmap, vmin=0, vmax=1)
        ax.set_xlabel("west_east")
        ax.set_ylabel("south_north")
    ax.set_title(title, loc="left", color=style.title_color, pad=14, fontweight="bold")
    if subtitle:
        ax.text(
            0.0,
            1.02,
            subtitle,
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            color=style.subtitle_color,
            fontsize=10.5,
        )
    ax.grid(True, color=style.grid_color, linestyle="--", linewidth=0.6, alpha=0.28)
    legend_handles = [
        Patch(facecolor=style.absent_color, edgecolor=style.legend_edgecolor, label=legend_labels[0]),
        Patch(facecolor=style.present_color, edgecolor=style.present_edge_color, label=legend_labels[1]),
    ]
    legend = ax.legend(
        handles=legend_handles,
        title=legend_title,
        loc="upper right",
        frameon=True,
        framealpha=0.95,
        facecolor=style.legend_facecolor,
        edgecolor=style.legend_edgecolor,
    )
    legend.get_title().set_color(style.title_color)
    for text in legend.get_texts():
        text.set_color(style.text_color)
    ax.tick_params(colors=style.text_color)
    if mesh is not None:
        mesh.set_rasterized(True)


def render_scalar_geographic_map(
    ax: plt.Axes,
    field: np.ndarray,
    *,
    title: str,
    subtitle: str | None = None,
    lon: np.ndarray | None = None,
    lat: np.ndarray | None = None,
    cbar_label: str = "Value",
    vmin: float = 0.0,
    vmax: float = 100.0,
    cmap: str = "magma",
    contour_levels: Sequence[float] | None = None,
    style: FinalProductMapStyle = DEFAULT_FINAL_PRODUCT_MAP_STYLE,
) -> None:
    scalar_field = np.asarray(field, dtype=np.float32)
    norm = Normalize(vmin=vmin, vmax=vmax)
    if lon is not None and lat is not None:
        _add_geographic_context(ax, lon=lon, lat=lat, style=style)
        mesh = ax.pcolormesh(
            lon,
            lat,
            scalar_field,
            shading="auto",
            cmap=cmap,
            norm=norm,
            transform=ccrs.PlateCarree(),
            zorder=1,
        )
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
        ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
        if contour_levels:
            levels = [level for level in contour_levels if vmin < level < vmax]
            if levels:
                ax.contour(
                    lon,
                    lat,
                    scalar_field,
                    levels=levels,
                    colors=style.present_edge_color,
                    linewidths=0.95,
                    alpha=0.5,
                    transform=ccrs.PlateCarree(),
                    zorder=2,
                )
    else:
        mesh = ax.imshow(scalar_field, origin="lower", cmap=cmap, norm=norm)
        ax.set_xlabel("west_east")
        ax.set_ylabel("south_north")
    ax.set_title(title, loc="left", color=style.title_color, pad=14, fontweight="bold")
    if subtitle:
        ax.text(
            0.0,
            1.02,
            subtitle,
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            color=style.subtitle_color,
            fontsize=10.5,
        )
    ax.grid(True, color=style.grid_color, linestyle="--", linewidth=0.6, alpha=0.28)
    cbar = ax.figure.colorbar(mesh, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label(cbar_label, color=style.title_color)
    cbar.ax.tick_params(colors=style.text_color)
    ax.tick_params(colors=style.text_color)
    if mesh is not None:
        mesh.set_rasterized(True)


def render_annotation_panel(
    ax: plt.Axes,
    title: str,
    lines: Sequence[str],
    *,
    footer: str | None = None,
    style: FinalProductMapStyle = DEFAULT_FINAL_PRODUCT_MAP_STYLE,
) -> None:
    ax.axis("off")
    text_lines = [title, ""] + list(lines)
    if footer:
        text_lines.extend(["", footer])
    ax.text(
        0.0,
        0.98,
        "\n".join(text_lines),
        transform=ax.transAxes,
        ha="left",
        va="top",
        color=style.text_color,
        fontsize=10.5,
        linespacing=1.3,
        bbox=style.annotation_box(),
    )


def render_compact_annotation_card(
    ax: plt.Axes,
    title: str,
    lines: Sequence[str],
    *,
    footer: str | None = None,
    style: FinalProductMapStyle = DEFAULT_FINAL_PRODUCT_MAP_STYLE,
) -> None:
    ax.set_axis_off()
    card = FancyBboxPatch(
        (0.04, 0.05),
        0.92,
        0.90,
        transform=ax.transAxes,
        boxstyle="round,pad=0.5",
        facecolor=style.annotation_facecolor,
        edgecolor=style.annotation_edgecolor,
        linewidth=1.0,
        alpha=style.info_box_alpha,
    )
    ax.add_patch(card)

    ax.text(
        0.10,
        0.92,
        title,
        transform=ax.transAxes,
        ha="left",
        va="top",
        color=style.title_color,
        fontsize=11.0,
        fontweight="bold",
    )

    top = 0.80
    bottom = 0.18 if footer else 0.12
    step = 0.0 if not lines else (top - bottom) / max(len(lines) - 1, 1)
    for index, line in enumerate(lines):
        y = top - (index * step if len(lines) > 1 else 0.0)
        ax.text(
            0.11,
            y,
            f"• {line}",
            transform=ax.transAxes,
            ha="left",
            va="top",
            color=style.text_color,
            fontsize=9.3,
            linespacing=1.15,
        )

    if footer:
        ax.text(
            0.10,
            0.08,
            footer,
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            color=style.footer_color,
            fontsize=8.5,
        )
