from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from .config import (
    FINAL_PRODUCT_CAVEAT_LABELS,
    FINAL_PRODUCT_OUTPUT_PREFIX,
    FINAL_PRODUCT_OUTPUT_PURPOSE,
    FINAL_PRODUCT_RENDER_VIEWS,
    FINAL_PRODUCT_REQUIRED_METADATA_FIELDS,
)
from .phase5 import Phase5ApproximateRiskProduct
from .phase6 import Phase6HeuristicSeverityProduct
from .presentation_map import (
    DEFAULT_FINAL_PRODUCT_MAP_STYLE,
    create_final_product_canvas,
    render_annotation_panel,
    render_binary_geographic_map,
    render_scalar_geographic_map,
)


@dataclass(frozen=True, slots=True)
class FinalProductArtifactContract:
    artifact_kind: str = FINAL_PRODUCT_OUTPUT_PURPOSE
    output_prefix: str = FINAL_PRODUCT_OUTPUT_PREFIX
    supported_views: tuple[str, ...] = FINAL_PRODUCT_RENDER_VIEWS
    required_metadata_fields: tuple[str, ...] = FINAL_PRODUCT_REQUIRED_METADATA_FIELDS
    caveat_labels: tuple[str, ...] = FINAL_PRODUCT_CAVEAT_LABELS

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_kind": self.artifact_kind,
            "output_prefix": self.output_prefix,
            "supported_views": list(self.supported_views),
            "required_metadata_fields": list(self.required_metadata_fields),
            "caveat_labels": list(self.caveat_labels),
        }


@dataclass(frozen=True, slots=True)
class FinalProductSummary:
    dataset_path: Path
    time_index: int
    time_label: str | None
    source_mode: str
    render_view: str
    source_phase: int
    source_phase_label: str
    source_product_kind: str
    map_field_kind: str
    map_semantics: str
    map_geographic_context: str = "Cartopy PlateCarree map with Natural Earth coastlines, borders, land and ocean context"
    output_purpose: str = FINAL_PRODUCT_OUTPUT_PURPOSE
    contract: FinalProductArtifactContract = field(default_factory=FinalProductArtifactContract)
    caveat_labels: tuple[str, ...] = FINAL_PRODUCT_CAVEAT_LABELS
    source_artifacts: dict[str, Path] = field(default_factory=dict)
    source_metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self, output_paths: dict[str, Path] | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "artifact_kind": self.contract.artifact_kind,
            "output_purpose": self.output_purpose,
            "dataset_path": str(self.dataset_path),
            "selected_time_index": self.time_index,
            "selected_time_label": self.time_label,
            "source_mode": self.source_mode,
            "render_view": self.render_view,
            "source_phase": self.source_phase,
            "source_phase_label": self.source_phase_label,
            "source_product_kind": self.source_product_kind,
            "map_field_kind": self.map_field_kind,
            "map_semantics": self.map_semantics,
            "map_geographic_context": self.map_geographic_context,
            "caveat_labels": list(self.caveat_labels),
            "contract": self.contract.to_dict(),
            "source_artifacts": {name: str(path) for name, path in self.source_artifacts.items()},
            "source_metrics": self.source_metrics,
        }
        if output_paths is not None:
            payload["outputs"] = {name: str(path) for name, path in output_paths.items()}
        return payload

    def to_markdown(self, output_paths: dict[str, Path] | None = None) -> str:
        def _format_value(value: Any) -> str:
            if isinstance(value, Path):
                return f"`{value}`"
            if isinstance(value, dict):
                return json.dumps(value, ensure_ascii=False, sort_keys=True)
            if isinstance(value, (list, tuple)):
                return ", ".join(_format_value(item).strip("`") for item in value)
            if value is None:
                return "unknown"
            return str(value)

        lines = [
            "# Producto final de presentacion",
            "",
            f"- Artifact contract: `{self.contract.artifact_kind}`",
            f"- Output purpose: `{self.output_purpose}`",
            f"- Source mode: `{self.source_mode}`",
            f"- Render view: `{self.render_view}`",
            f"- Source phase: Phase {self.source_phase} ({self.source_phase_label})",
            f"- Source product kind: {self.source_product_kind}",
            f"- Map field kind: {self.map_field_kind}",
            f"- Map semantics: {self.map_semantics}",
            f"- Map geographic context: {self.map_geographic_context}",
            f"- Dataset: `{self.dataset_path}`",
            f"- selected_time_index: {self.time_index}",
            f"- selected_time_label: {self.time_label or 'unknown'}",
            f"- Caveats: {', '.join(self.caveat_labels)}",
            "",
            "## Contract",
            f"- Output prefix: `{self.contract.output_prefix}`",
            f"- Supported views: {', '.join(self.contract.supported_views)}",
            f"- Required metadata fields: {', '.join(self.contract.required_metadata_fields)}",
            "",
            "## Source artifacts",
        ]
        if self.source_artifacts:
            for name, path in self.source_artifacts.items():
                lines.append(f"- {name}: `{path}`")
        else:
            lines.append("- none")
        lines.extend(["", "## Source metrics"])
        if self.source_metrics:
            for name, value in self.source_metrics.items():
                lines.append(f"- {name}: {_format_value(value)}")
        else:
            lines.append("- none")
        if output_paths:
            lines.extend(["", "## Outputs"])
            for name, path in output_paths.items():
                lines.append(f"- {name}: `{path}`")
        return "\n".join(lines)


def _coerce_source_artifacts(source_artifacts: Mapping[str, Path] | None) -> dict[str, Path]:
    if not source_artifacts:
        return {}
    return {name: Path(path) for name, path in source_artifacts.items()}


def _risk_source_metrics(product: Phase5ApproximateRiskProduct) -> dict[str, Any]:
    return {
        "liquid_horizontal_fraction": product.liquid_horizontal_fraction,
        "liquid_vertical_fraction": product.liquid_vertical_fraction,
        "risk_horizontal_fraction": product.risk_horizontal_fraction,
        "risk_vertical_fraction": product.risk_vertical_fraction,
        "has_liquid": product.has_liquid,
        "has_risk": product.has_risk,
        "theta_range_k": [product.theta_min_k, product.theta_max_k],
        "pressure_proxy_range_pa": [product.pressure_proxy_min_pa, product.pressure_proxy_max_pa],
        "temperature_proxy_range_k": [product.temperature_proxy_min_k, product.temperature_proxy_max_k],
        "approximation_notes": list(product.approximation_notes),
    }


def _severity_source_metrics(product: Phase6HeuristicSeverityProduct) -> dict[str, Any]:
    return {
        "severity_class": product.severity_class,
        "severity_score": product.severity_score,
        "dominant_band": product.dominant_band,
        "persistence_fraction": product.persistence_fraction,
        "selected_active_level_ranges": list(product.selected_active_level_ranges),
        "selected_time_risk_fraction": float(product.time_risk_horizontal_fraction.values[product.time_index]),
        "selected_time_liquid_fraction": float(product.time_liquid_horizontal_fraction.values[product.time_index]),
        "selected_time_mixed_fraction": float(product.time_mixed_horizontal_fraction.values[product.time_index]),
        "heuristic_notes": list(product.heuristic_notes),
    }


def _build_spatial_heuristic_severity_field(
    source_dataset: xr.Dataset,
    risk_product: Phase5ApproximateRiskProduct,
) -> tuple[xr.DataArray, dict[str, Any]]:
    selected = source_dataset.isel(Time=risk_product.time_index)
    if "QICE" not in selected:
        raise ValueError("heuristic-severity rendering requires QICE for the spatial mixed-phase score.")

    liquid_3d = (selected["QCLOUD"].fillna(0) + selected["QRAIN"].fillna(0) > 0).astype(np.float32)
    ice_3d = (selected["QICE"].fillna(0) > 0).astype(np.float32)
    mixed_3d = (liquid_3d > 0) & (ice_3d > 0)
    risk_3d = risk_product.risk_presence_3d.astype(np.float32)

    risk_fraction = risk_3d.mean(dim="bottom_top")
    liquid_fraction = liquid_3d.mean(dim="bottom_top")
    mixed_fraction = mixed_3d.astype(np.float32).mean(dim="bottom_top")
    coherence_fraction = 1.0 - np.abs(risk_fraction - liquid_fraction)

    score = (
        0.50 * risk_fraction
        + 0.25 * liquid_fraction
        + 0.15 * mixed_fraction
        + 0.10 * coherence_fraction
    ) * 100.0
    score = score.clip(0.0, 100.0).astype(np.float32)
    score.name = "spatial_heuristic_severity_score"
    score.attrs.update(
        {
            "description": "2D heuristic severity score per cell derived from Phase 5 risk/liquid overlap and mixed-phase presence.",
            "score_range": "0 to 100",
            "score_formula": (
                "100 * (0.50*risk_vertical_fraction + 0.25*liquid_vertical_fraction + "
                "0.15*mixed_vertical_fraction + 0.10*coherence_fraction)"
            ),
        }
    )

    stats = {
        "score_min": float(score.min().item()),
        "score_max": float(score.max().item()),
        "score_mean": float(score.mean().item()),
        "risk_vertical_mean": float(risk_fraction.mean().item()),
        "liquid_vertical_mean": float(liquid_fraction.mean().item()),
        "mixed_vertical_mean": float(mixed_fraction.mean().item()),
        "coherence_mean": float(coherence_fraction.mean().item()),
        "score_formula": score.attrs["score_formula"],
    }
    return score, stats


def _final_product_annotation_lines(
    summary: FinalProductSummary,
    risk_product: Phase5ApproximateRiskProduct,
    *,
    map_semantics: str,
    severity_product: Phase6HeuristicSeverityProduct | None = None,
    spatial_severity_stats: dict[str, Any] | None = None,
) -> tuple[str, ...]:
    lines: list[str] = [
        f"Render view: {summary.render_view}",
        f"Source phase: Phase {summary.source_phase} ({summary.source_phase_label})",
        f"Source product kind: {summary.source_product_kind}",
        f"Map field kind: {summary.map_field_kind}",
        f"Map semantics: {map_semantics}",
        f"Selected time: {summary.time_index} ({summary.time_label or 'unknown'})",
    ]

    risk_metrics = summary.source_metrics if summary.render_view == "approximate-risk" else _risk_source_metrics(risk_product)
    lines.append(f"Approximate-risk coverage: {risk_metrics['risk_horizontal_fraction']:.1%}")
    lines.append(f"Liquid coverage: {risk_metrics['liquid_horizontal_fraction']:.1%}")
    lines.append(f"Geographic context: {summary.map_geographic_context}")

    lon = risk_product.risk_presence.coords.get("XLONG")
    lat = risk_product.risk_presence.coords.get("XLAT")
    if lon is not None and lat is not None:
        lon_values = lon.values
        lat_values = lat.values
        lines.append(
            "Domain longitude: "
            f"{float(lon_values.min()):.2f} to {float(lon_values.max()):.2f}"
        )
        lines.append(
            "Domain latitude: "
            f"{float(lat_values.min()):.2f} to {float(lat_values.max()):.2f}"
        )

    if summary.render_view == "heuristic-severity" and severity_product is not None:
        lines.append(f"Severity class: {severity_product.severity_class} ({severity_product.severity_score:.1f}/100)")
        lines.append(f"Dominant band: {severity_product.dominant_band}")
        lines.append(f"Persistence fraction: {severity_product.persistence_fraction:.1%}")
        if spatial_severity_stats is not None:
            lines.append(
                "Spatial score range: "
                f"{spatial_severity_stats['score_min']:.1f} to {spatial_severity_stats['score_max']:.1f}"
            )
            lines.append(f"Spatial score mean: {spatial_severity_stats['score_mean']:.1f}")
            lines.append(f"Spatial score formula: {spatial_severity_stats['score_formula']}")
        lines.append("Map source: Phase 5 column overlap projected into a 2D severity score")

    lines.extend(
        [
            "Caveats:",
            *[f"- {label}" for label in summary.caveat_labels],
        ]
    )
    return tuple(lines)


def build_final_product_figure(
    summary: FinalProductSummary,
    risk_product: Phase5ApproximateRiskProduct,
    severity_product: Phase6HeuristicSeverityProduct | None = None,
    source_dataset: xr.Dataset | None = None,
    *,
    style=DEFAULT_FINAL_PRODUCT_MAP_STYLE,
):
    if summary.render_view not in FINAL_PRODUCT_RENDER_VIEWS:
        raise ValueError(f"Unsupported final-product render view: {summary.render_view}")
    if summary.render_view == "heuristic-severity" and severity_product is None:
        raise ValueError("heuristic-severity final products require the phase-6 severity product.")
    if summary.render_view == "heuristic-severity" and source_dataset is None:
        raise ValueError("heuristic-severity final products require the source dataset to build the spatial score.")

    fig, map_ax, annotation_ax = create_final_product_canvas(style)
    lon = risk_product.risk_presence.coords.get("XLONG")
    lat = risk_product.risk_presence.coords.get("XLAT")
    if summary.render_view == "approximate-risk":
        risk_field = risk_product.risk_presence.astype("uint8").values
        title = "Presentation map - approximate-risk footprint"
        legend_title = "Approximate-risk footprint"
        subtitle_suffix = "binary risk footprint"
        subtitle_parts = [
            f"Time {summary.time_index}",
            summary.time_label or "unknown time",
            f"Source phase {summary.source_phase}",
            subtitle_suffix,
        ]
        render_binary_geographic_map(
            map_ax,
            risk_field,
            title=title,
            subtitle=" | ".join(subtitle_parts),
            lon=lon.values if lon is not None else None,
            lat=lat.values if lat is not None else None,
            legend_title=legend_title,
            legend_labels=("Absent", "Present"),
            style=style,
        )
        spatial_severity_stats = None
    else:
        assert source_dataset is not None
        spatial_severity_field, spatial_severity_stats = _build_spatial_heuristic_severity_field(source_dataset, risk_product)
        title = "Presentation map - spatial heuristic severity score"
        subtitle_parts = [
            f"Time {summary.time_index}",
            summary.time_label or "unknown time",
            f"Source phase {summary.source_phase}",
            f"Severity {severity_product.severity_class} ({severity_product.severity_score:.1f}/100)",
        ]
        render_scalar_geographic_map(
            map_ax,
            spatial_severity_field.values,
            title=title,
            subtitle=" | ".join(subtitle_parts),
            lon=lon.values if lon is not None else None,
            lat=lat.values if lat is not None else None,
            cbar_label="Spatial heuristic severity score (0-100)",
            vmin=0.0,
            vmax=100.0,
            contour_levels=(20.0, 40.0, 60.0, 80.0),
            style=style,
        )
    annotation_lines = _final_product_annotation_lines(
        summary,
        risk_product,
        map_semantics=summary.map_semantics,
        severity_product=severity_product,
        spatial_severity_stats=spatial_severity_stats,
    )
    render_annotation_panel(
        annotation_ax,
        "Final product annotations",
        annotation_lines,
        footer="Presentation artifact built from diagnostic proxy outputs.",
        style=style,
    )
    fig.suptitle(
        "Riesgo de engelamiento - producto final de presentacion",
        color=style.title_color,
        fontsize=16,
        fontweight="bold",
    )
    return fig


def build_final_product_summary(
    source_product: Phase5ApproximateRiskProduct | Phase6HeuristicSeverityProduct,
    dataset_path: str | Path,
    *,
    render_view: str,
    source_artifacts: Mapping[str, Path] | None = None,
) -> FinalProductSummary:
    source_artifacts_map = _coerce_source_artifacts(source_artifacts)
    dataset_path = Path(dataset_path)

    if render_view == "approximate-risk":
        if not isinstance(source_product, Phase5ApproximateRiskProduct):
            raise ValueError("approximate-risk final products must be built from the phase-5 proxy product.")
        return FinalProductSummary(
            dataset_path=dataset_path,
            time_index=source_product.time_index,
            time_label=source_product.time_label,
            source_mode=render_view,
            render_view=render_view,
            source_phase=5,
            source_phase_label="approximate icing risk",
            source_product_kind="approximate proxy",
            map_field_kind="Phase 5 approximate-risk footprint",
            map_semantics="binary approximate-risk footprint rendered directly from Phase 5",
            map_geographic_context="Cartopy PlateCarree map with Natural Earth borders and coastlines framing the selected WRF domain",
            source_artifacts=source_artifacts_map,
            source_metrics=_risk_source_metrics(source_product),
        )

    if render_view == "heuristic-severity":
        if not isinstance(source_product, Phase6HeuristicSeverityProduct):
            raise ValueError("heuristic-severity final products must be built from the phase-6 severity product.")
        return FinalProductSummary(
            dataset_path=dataset_path,
            time_index=source_product.time_index,
            time_label=source_product.time_label,
            source_mode=render_view,
            render_view=render_view,
            source_phase=6,
            source_phase_label="heuristic severity",
            source_product_kind="heuristic proxy",
            map_field_kind="Spatial heuristic severity score",
            map_semantics=(
                "2D heuristic severity score per cell derived from Phase 5 risk/liquid overlap, "
                "mixed-phase presence, and coherence at the selected time"
            ),
            map_geographic_context="Cartopy PlateCarree map with Natural Earth borders and coastlines framing the selected WRF domain",
            source_artifacts=source_artifacts_map,
            source_metrics=_severity_source_metrics(source_product),
        )

    raise ValueError(f"Unsupported final-product render view: {render_view}")


def _view_slug(render_view: str) -> str:
    return render_view.replace("-", "_")


def write_final_product_outputs(
    summary: FinalProductSummary,
    output_dir: str | Path,
    *,
    risk_product: Phase5ApproximateRiskProduct,
    severity_product: Phase6HeuristicSeverityProduct | None = None,
    source_dataset: xr.Dataset | None = None,
) -> tuple[Path, Path, Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    base_name = f"{FINAL_PRODUCT_OUTPUT_PREFIX}_t{summary.time_index:03d}_{_view_slug(summary.render_view)}"
    markdown_path = output_path / f"{base_name}.md"
    json_path = output_path / f"{base_name}.json"
    png_path = output_path / f"{base_name}.png"

    output_paths = {
        "markdown": markdown_path,
        "json": json_path,
        "png": png_path,
    }

    markdown_path.write_text(summary.to_markdown(output_paths), encoding="utf-8")
    json_path.write_text(json.dumps(summary.to_dict(output_paths), indent=2, ensure_ascii=False), encoding="utf-8")
    figure = build_final_product_figure(summary, risk_product, severity_product, source_dataset)
    figure.savefig(png_path, dpi=DEFAULT_FINAL_PRODUCT_MAP_STYLE.dpi, facecolor=DEFAULT_FINAL_PRODUCT_MAP_STYLE.figure_facecolor)
    plt.close(figure)

    return markdown_path, json_path, png_path
