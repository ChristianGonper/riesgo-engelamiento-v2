from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import matplotlib
import numpy as np
from matplotlib.colors import Normalize
from matplotlib.colors import ListedColormap
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
    grid = fig.add_gridspec(1, 2, width_ratios=[3.4, 1.25])
    map_ax = fig.add_subplot(grid[0, 0])
    annotation_ax = fig.add_subplot(grid[0, 1])
    map_ax.set_facecolor(style.map_facecolor)
    annotation_ax.set_facecolor(style.figure_facecolor)
    return fig, map_ax, annotation_ax


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
        mesh = ax.pcolormesh(lon, lat, binary_field, shading="auto", cmap=cmap, vmin=0, vmax=1)
        if np.any(binary_field > 0):
            ax.contour(lon, lat, binary_field, levels=[0.5], colors=style.present_edge_color, linewidths=1.25)
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
        mesh = ax.pcolormesh(lon, lat, scalar_field, shading="auto", cmap=cmap, norm=norm)
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
        ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
        if contour_levels:
            levels = [level for level in contour_levels if vmin < level < vmax]
            if levels:
                ax.contour(lon, lat, scalar_field, levels=levels, colors=style.present_edge_color, linewidths=0.95, alpha=0.5)
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
