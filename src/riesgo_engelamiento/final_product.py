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
    FINAL_PRODUCT_VERTICAL_BAND_CHOICES,
    FINAL_PRODUCT_VERTICAL_BAND_MEANINGS,
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
    selected_band_request: str = "dominant"
    selected_band: str = "lower"
    selected_band_resolution: str = "dominant"
    selected_band_eta_range: tuple[float, float] | None = None
    selected_band_level_count: int = 0
    selected_band_meaning: str = ""
    selected_band_signal_status: str = "empty"
    dominant_band: str = "none"
    dominant_band_eta_range: tuple[float, float] | None = None
    dominant_band_level_count: int = 0
    dominant_band_meaning: str = ""
    band_relation: str = "no dominant band detected"
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
            "selected_band_request": self.selected_band_request,
            "selected_band": self.selected_band,
            "selected_band_resolution": self.selected_band_resolution,
            "selected_band_eta_range": list(self.selected_band_eta_range) if self.selected_band_eta_range is not None else None,
            "selected_band_level_count": self.selected_band_level_count,
            "selected_band_meaning": self.selected_band_meaning,
            "selected_band_signal_status": self.selected_band_signal_status,
            "dominant_band": self.dominant_band,
            "dominant_band_eta_range": list(self.dominant_band_eta_range) if self.dominant_band_eta_range is not None else None,
            "dominant_band_level_count": self.dominant_band_level_count,
            "dominant_band_meaning": self.dominant_band_meaning,
            "band_relation": self.band_relation,
            "presentation_summary": self.presentation_summary_text(),
            "comparative_summary": self.comparative_summary_text(),
            "aircraft_interpretation": self.aircraft_interpretation_text(),
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
            "## Presentation summary",
            self.presentation_summary_text(),
            "",
            "## Comparative summary",
            self.comparative_summary_text(),
            "",
            "## Aircraft-oriented interpretation",
            self.aircraft_interpretation_text(),
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
            f"- Selected band request: {self.selected_band_request}",
            f"- Selected band: {self.selected_band}",
            f"- Selected band resolution: {self.selected_band_resolution}",
            f"- Selected band eta range: {self._format_range(self.selected_band_eta_range)}",
            f"- Selected band level count: {self.selected_band_level_count}",
            f"- Selected band meaning: {self.selected_band_meaning}",
            f"- Selected band signal status: {self.selected_band_signal_status}",
            f"- Dominant band: {self.dominant_band}",
            f"- Dominant band eta range: {self._format_range(self.dominant_band_eta_range)}",
            f"- Dominant band level count: {self.dominant_band_level_count}",
            f"- Dominant band meaning: {self.dominant_band_meaning}",
            f"- Band relation: {self.band_relation}",
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

    @staticmethod
    def _format_range(value: tuple[float, float] | None) -> str:
        if value is None:
            return "unknown"
        return f"{value[0]:.2f} -> {value[1]:.2f}"

    def _coverage_summary(self) -> str:
        metrics = self.source_metrics
        parts: list[str] = []

        if self.render_view == "approximate-risk":
            selected_band_horizontal_fraction = metrics.get("selected_band_horizontal_fraction")
            if selected_band_horizontal_fraction is not None:
                parts.append(f"selected-band coverage {float(selected_band_horizontal_fraction):.1%}")
            selected_band_risk_fraction = metrics.get("selected_band_risk_fraction")
            if selected_band_risk_fraction is not None:
                parts.append(f"selected-band risk {float(selected_band_risk_fraction):.1%}")
        else:
            severity_class = metrics.get("severity_class") or self.source_metrics.get("severity_class")
            severity_score = metrics.get("severity_score")
            if severity_class is not None and severity_score is not None:
                parts.append(f"severity {severity_class} ({float(severity_score):.1f}/100)")
            selected_band_mean_risk_fraction = metrics.get("selected_band_mean_risk_fraction")
            if selected_band_mean_risk_fraction is not None:
                parts.append(f"selected-band mean risk {float(selected_band_mean_risk_fraction):.1%}")

        risk_horizontal_fraction = metrics.get("risk_horizontal_fraction")
        if risk_horizontal_fraction is not None:
            parts.append(f"domain risk {float(risk_horizontal_fraction):.1%}")
        liquid_horizontal_fraction = metrics.get("liquid_horizontal_fraction")
        if liquid_horizontal_fraction is not None:
            parts.append(f"domain liquid {float(liquid_horizontal_fraction):.1%}")

        if not parts:
            return "coverage unavailable"
        return "; ".join(parts)

    def presentation_summary_text(self) -> str:
        return (
            f"Mode selected: {self.render_view}. "
            f"Rendered band: {self.selected_band} ({self.selected_band_resolution}); "
            f"dominant band: {self.dominant_band}; "
            f"{self.band_relation}; "
            f"{self._coverage_summary()}. "
            "Caveats: proxy-only, model-relative eta bands, no exact altitude."
        )

    def comparative_summary_text(self) -> str:
        if self.render_view == "approximate-risk":
            return (
                "Approximate-risk is the binary Phase 5 proxy footprint; heuristic-severity keeps the same "
                "selected time and band context but adds a graded score from risk/liquid overlap, mixed-phase "
                "presence and coherence. The severity view adds structure, not operational certainty."
            )
        return (
            "Heuristic-severity adds a graded, band-conditioned score to the Phase 5 proxy footprint; "
            "approximate-risk stays binary and shows where the proxy is present without ranking intensity. "
            "Both remain presentation-oriented proxy views."
        )

    def aircraft_interpretation_text(self) -> str:
        return (
            f"Aircraft-oriented reading: the {self.selected_band} band is a model-relative layer, not a flight level. "
            "Use it to compare relative vertical structure and spatial extent only; this is not operational icing "
            "guidance, route advice, or exact altitude inference."
        )


def _coerce_source_artifacts(source_artifacts: Mapping[str, Path] | None) -> dict[str, Path]:
    if not source_artifacts:
        return {}
    return {name: Path(path) for name, path in source_artifacts.items()}


def _band_lookup(product: Phase6HeuristicSeverityProduct) -> dict[str, Any]:
    return {band.name: band for band in product.band_summaries}


def _band_meaning(band_name: str) -> str:
    return FINAL_PRODUCT_VERTICAL_BAND_MEANINGS.get(
        band_name,
        "Dominant relative eta band detected from the selected time",
    )


def _band_signal_status(
    selected_risk_fraction: float,
    selected_liquid_fraction: float,
    selected_mixed_fraction: float,
    level_count: int,
) -> str:
    if level_count == 0:
        return "empty"
    peak_fraction = max(selected_risk_fraction, selected_liquid_fraction, selected_mixed_fraction)
    if peak_fraction == 0.0:
        return "empty"
    if peak_fraction < 0.05:
        return "low-signal"
    return "active"


def _resolve_band_selection(
    requested_band: str,
    severity_product: Phase6HeuristicSeverityProduct,
) -> tuple[str, str, Any | None, Any | None, str, str, str, str]:
    band_map = _band_lookup(severity_product)
    if not band_map:
        raise ValueError("Cannot resolve vertical bands without phase-6 band summaries.")

    dominant_band_name = severity_product.dominant_band if severity_product.dominant_band in band_map else "none"
    dominant_band = band_map.get(dominant_band_name)

    if requested_band == "dominant":
        if dominant_band_name != "none" and dominant_band is not None:
            selected_band_name = dominant_band_name
            resolution = "dominant"
        else:
            selected_band_name = "lower" if "lower" in band_map else next(iter(band_map))
            resolution = "dominant-fallback"
    else:
        if requested_band not in band_map:
            raise ValueError(
                f"Unsupported vertical band: {requested_band}. Available bands: {', '.join(sorted(band_map))}"
            )
        selected_band_name = requested_band
        resolution = "explicit"

    selected_band = band_map[selected_band_name]
    selected_meaning = _band_meaning(selected_band_name)
    dominant_meaning = _band_meaning(dominant_band_name) if dominant_band_name != "none" else "No dominant band detected"
    if dominant_band_name == "none":
        relation = (
            f"no dominant band detected; rendered fallback band {selected_band_name}"
            if resolution == "dominant-fallback"
            else "no dominant band detected"
        )
    elif selected_band_name == dominant_band_name:
        relation = f"selected band matches dominant band {dominant_band_name}"
    else:
        relation = f"selected band {selected_band_name} differs from dominant band {dominant_band_name}"

    selected_signal_status = _band_signal_status(
        selected_band.selected_risk_fraction,
        selected_band.selected_liquid_fraction,
        selected_band.selected_mixed_fraction,
        selected_band.level_count,
    )
    return selected_band_name, resolution, selected_band, dominant_band, relation, selected_meaning, dominant_meaning, selected_signal_status


def _band_metadata_payload(
    *,
    requested_band: str,
    selected_band_name: str,
    selected_resolution: str,
    selected_band: Any | None,
    dominant_band: Any | None,
    relation: str,
    selected_meaning: str,
    dominant_meaning: str,
    selected_signal_status: str,
) -> dict[str, Any]:
    payload = {
        "selected_band_request": requested_band,
        "selected_band": selected_band_name,
        "selected_band_resolution": selected_resolution,
        "selected_band_eta_range": None if selected_band is None else (float(selected_band.eta_min), float(selected_band.eta_max)),
        "selected_band_level_count": 0 if selected_band is None else int(selected_band.level_count),
        "selected_band_meaning": selected_meaning,
        "selected_band_signal_status": selected_signal_status,
        "dominant_band": "none" if dominant_band is None else dominant_band.name,
        "dominant_band_eta_range": None if dominant_band is None else (float(dominant_band.eta_min), float(dominant_band.eta_max)),
        "dominant_band_level_count": 0 if dominant_band is None else int(dominant_band.level_count),
        "dominant_band_meaning": dominant_meaning,
        "band_relation": relation,
    }
    return payload


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
        "risk_horizontal_fraction": float(product.time_risk_horizontal_fraction.values[product.time_index]),
        "liquid_horizontal_fraction": float(product.time_liquid_horizontal_fraction.values[product.time_index]),
        "mixed_horizontal_fraction": float(product.time_mixed_horizontal_fraction.values[product.time_index]),
        "active_level_fraction": float(product.time_active_level_fraction.values[product.time_index]),
        "selected_active_level_ranges": list(product.selected_active_level_ranges),
        "selected_time_risk_fraction": float(product.time_risk_horizontal_fraction.values[product.time_index]),
        "selected_time_liquid_fraction": float(product.time_liquid_horizontal_fraction.values[product.time_index]),
        "selected_time_mixed_fraction": float(product.time_mixed_horizontal_fraction.values[product.time_index]),
        "heuristic_notes": list(product.heuristic_notes),
    }


def _selected_band_mask(eta_mid: xr.DataArray, band_name: str) -> xr.DataArray:
    eta_values = eta_mid.values
    if band_name == "upper":
        mask = eta_values >= 0.66
    elif band_name == "middle":
        mask = (eta_values >= 0.33) & (eta_values < 0.66)
    elif band_name == "lower":
        mask = eta_values < 0.33
    else:
        raise ValueError(f"Unsupported vertical band: {band_name}")
    return xr.DataArray(mask.astype(bool), dims=("bottom_top",), coords={"bottom_top": eta_mid.coords["bottom_top"]})


def _build_band_conditioned_risk_field(
    risk_product: Phase5ApproximateRiskProduct,
    band_name: str,
) -> tuple[xr.DataArray, dict[str, Any]]:
    eta_mid = risk_product.risk_presence_3d.coords.get("eta_mid")
    if eta_mid is None:
        raise ValueError("risk-product vertical coordinates are missing eta_mid.")
    band_mask = _selected_band_mask(eta_mid, band_name)
    band_risk = risk_product.risk_presence_3d.astype(bool).where(band_mask, other=False)
    band_risk_presence = band_risk.any(dim="bottom_top").astype(np.uint8)
    band_risk_presence.name = "band_conditioned_approximate_risk"
    stats = {
        "selected_band": band_name,
        "selected_band_level_count": int(band_mask.sum().item()),
        "selected_band_risk_fraction": float(band_risk.mean(dim="bottom_top").mean().item()),
        "selected_band_horizontal_fraction": float(band_risk_presence.mean().item()) if band_risk_presence.size else 0.0,
    }
    band_risk_presence.attrs.update(
        {
            "description": "Band-conditioned 2D approximate-risk footprint derived from Phase 5 risk presence.",
            "selected_band": band_name,
        }
    )
    return band_risk_presence, stats


def _build_band_conditioned_heuristic_severity_field(
    source_dataset: xr.Dataset,
    risk_product: Phase5ApproximateRiskProduct,
    band_name: str,
) -> tuple[xr.DataArray, dict[str, Any]]:
    selected = source_dataset.isel(Time=risk_product.time_index)
    if "QICE" not in selected:
        raise ValueError("heuristic-severity rendering requires QICE for the spatial mixed-phase score.")

    eta_mid = risk_product.risk_presence_3d.coords.get("eta_mid")
    if eta_mid is None:
        raise ValueError("risk-product vertical coordinates are missing eta_mid.")
    band_mask = _selected_band_mask(eta_mid, band_name)

    liquid_3d = (selected["QCLOUD"].fillna(0) + selected["QRAIN"].fillna(0) > 0).astype(np.float32)
    ice_3d = (selected["QICE"].fillna(0) > 0).astype(np.float32)
    mixed_3d = (liquid_3d > 0) & (ice_3d > 0)
    risk_3d = risk_product.risk_presence_3d.astype(np.float32)

    band_risk = risk_3d.where(band_mask, other=0.0)
    band_liquid = liquid_3d.where(band_mask, other=0.0)
    band_mixed = mixed_3d.astype(np.float32).where(band_mask, other=0.0)

    risk_fraction = band_risk.mean(dim="bottom_top")
    liquid_fraction = band_liquid.mean(dim="bottom_top")
    mixed_fraction = band_mixed.mean(dim="bottom_top")
    coherence_fraction = 1.0 - np.abs(risk_fraction - liquid_fraction)

    score = (
        0.50 * risk_fraction
        + 0.25 * liquid_fraction
        + 0.15 * mixed_fraction
        + 0.10 * coherence_fraction
    ) * 100.0
    score = score.clip(0.0, 100.0).astype(np.float32)
    score.name = "band_conditioned_spatial_heuristic_severity_score"
    score.attrs.update(
        {
            "description": "2D heuristic severity score per cell derived from Phase 5 risk/liquid overlap and mixed-phase presence within the selected model-relative band.",
            "score_range": "0 to 100",
            "selected_band": band_name,
            "score_formula": (
                "100 * (0.50*risk_vertical_fraction + 0.25*liquid_vertical_fraction + "
                "0.15*mixed_vertical_fraction + 0.10*coherence_fraction)"
            ),
        }
    )

    stats = {
        "selected_band": band_name,
        "selected_band_level_count": int(band_mask.sum().item()),
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
        f"Presentation summary: {summary.presentation_summary_text()}",
        f"Comparative summary: {summary.comparative_summary_text()}",
        f"Aircraft-oriented interpretation: {summary.aircraft_interpretation_text()}",
        "",
        f"Render view: {summary.render_view}",
        f"Source phase: Phase {summary.source_phase} ({summary.source_phase_label})",
        f"Source product kind: {summary.source_product_kind}",
        f"Map field kind: {summary.map_field_kind}",
        f"Map semantics: {map_semantics}",
        f"Selected time: {summary.time_index} ({summary.time_label or 'unknown'})",
        f"Selected band request: {summary.selected_band_request}",
        f"Selected band: {summary.selected_band}",
        f"Selected band resolution: {summary.selected_band_resolution}",
        f"Selected band eta range: {FinalProductSummary._format_range(summary.selected_band_eta_range)}",
        f"Selected band meaning: {summary.selected_band_meaning}",
        f"Selected band signal status: {summary.selected_band_signal_status}",
        f"Dominant band: {summary.dominant_band}",
        f"Dominant band eta range: {FinalProductSummary._format_range(summary.dominant_band_eta_range)}",
        f"Dominant band meaning: {summary.dominant_band_meaning}",
        f"Band relation: {summary.band_relation}",
    ]

    risk_metrics = summary.source_metrics
    lines.append(f"Domain approximate-risk coverage: {risk_metrics['risk_horizontal_fraction']:.1%}")
    lines.append(f"Domain liquid coverage: {risk_metrics['liquid_horizontal_fraction']:.1%}")
    if risk_metrics.get("selected_band_risk_fraction") is not None:
        lines.append(f"Selected-band risk fraction: {float(risk_metrics['selected_band_risk_fraction']):.1%}")
    if risk_metrics.get("selected_band_liquid_fraction") is not None:
        lines.append(f"Selected-band liquid fraction: {float(risk_metrics['selected_band_liquid_fraction']):.1%}")
    if risk_metrics.get("selected_band_mixed_fraction") is not None:
        lines.append(f"Selected-band mixed fraction: {float(risk_metrics['selected_band_mixed_fraction']):.1%}")
    if risk_metrics.get("selected_band_mean_risk_fraction") is not None:
        lines.append(f"Selected-band mean risk fraction: {float(risk_metrics['selected_band_mean_risk_fraction']):.1%}")
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
        lines.append(f"Dominant band (phase 6): {severity_product.dominant_band}")
        lines.append(f"Persistence fraction: {severity_product.persistence_fraction:.1%}")
        if spatial_severity_stats is not None:
            lines.append(
                "Band score range: "
                f"{spatial_severity_stats['score_min']:.1f} to {spatial_severity_stats['score_max']:.1f}"
            )
            lines.append(f"Band score mean: {spatial_severity_stats['score_mean']:.1f}")
            lines.append(f"Band score formula: {spatial_severity_stats['score_formula']}")
        lines.append("Map source: Phase 5 column overlap projected into a band-conditioned 2D severity score")
    elif summary.render_view == "approximate-risk" and spatial_severity_stats is not None:
        if spatial_severity_stats.get("selected_band_horizontal_fraction") is not None:
            lines.append(
                "Selected-band horizontal coverage: "
                f"{float(spatial_severity_stats['selected_band_horizontal_fraction']):.1%}"
            )
        if spatial_severity_stats.get("selected_band_level_count") is not None:
            lines.append(
                "Selected-band level count: "
                f"{int(spatial_severity_stats['selected_band_level_count'])}"
            )
        lines.append("Map source: Phase 5 risk footprint projected into a band-conditioned binary view")

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
        risk_field, band_stats = _build_band_conditioned_risk_field(risk_product, summary.selected_band)
        title = f"Presentation map - approximate-risk footprint ({summary.selected_band} band)"
        legend_title = f"Approximate-risk footprint ({summary.selected_band} band)"
        subtitle_parts = [
            f"Time {summary.time_index}",
            summary.time_label or "unknown time",
            f"Selected band {summary.selected_band}",
            f"Dominant {summary.dominant_band}",
            f"Source phase {summary.source_phase}",
            f"Resolution {summary.selected_band_resolution}",
        ]
        render_binary_geographic_map(
            map_ax,
            risk_field.values,
            title=title,
            subtitle=" | ".join(subtitle_parts),
            lon=lon.values if lon is not None else None,
            lat=lat.values if lat is not None else None,
            legend_title=legend_title,
            legend_labels=("No risk in band", "Risk in band"),
            style=style,
        )
        spatial_severity_stats = band_stats
    else:
        assert source_dataset is not None
        spatial_severity_field, spatial_severity_stats = _build_band_conditioned_heuristic_severity_field(
            source_dataset,
            risk_product,
            summary.selected_band,
        )
        title = f"Presentation map - band-conditioned spatial heuristic severity score ({summary.selected_band} band)"
        subtitle_parts = [
            f"Time {summary.time_index}",
            summary.time_label or "unknown time",
            f"Selected band {summary.selected_band}",
            f"Dominant {summary.dominant_band}",
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
            cbar_label="Band-conditioned heuristic severity score (0-100)",
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
        f"Riesgo de engelamiento - producto final de presentacion ({summary.selected_band} band)",
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
    selected_band: str = "dominant",
    severity_product: Phase6HeuristicSeverityProduct | None = None,
    source_artifacts: Mapping[str, Path] | None = None,
) -> FinalProductSummary:
    source_artifacts_map = _coerce_source_artifacts(source_artifacts)
    dataset_path = Path(dataset_path)
    reference_severity_product = severity_product
    if reference_severity_product is None and isinstance(source_product, Phase6HeuristicSeverityProduct):
        reference_severity_product = source_product
    if reference_severity_product is None:
        raise ValueError("Final-product band reporting requires the phase-6 severity product.")
    if selected_band not in FINAL_PRODUCT_VERTICAL_BAND_CHOICES:
        raise ValueError(
            f"Unsupported final-product band request: {selected_band}. "
            f"Available choices: {', '.join(FINAL_PRODUCT_VERTICAL_BAND_CHOICES)}"
        )
    (
        resolved_band_name,
        band_resolution,
        resolved_band,
        dominant_band,
        band_relation,
        resolved_band_meaning,
        dominant_band_meaning,
        resolved_band_signal_status,
    ) = _resolve_band_selection(selected_band, reference_severity_product)
    band_metadata = _band_metadata_payload(
        requested_band=selected_band,
        selected_band_name=resolved_band_name,
        selected_resolution=band_resolution,
        selected_band=resolved_band,
        dominant_band=dominant_band,
        relation=band_relation,
        selected_meaning=resolved_band_meaning,
        dominant_meaning=dominant_band_meaning,
        selected_signal_status=resolved_band_signal_status,
    )

    if render_view == "approximate-risk":
        if not isinstance(source_product, Phase5ApproximateRiskProduct):
            raise ValueError("approximate-risk final products must be built from the phase-5 proxy product.")
        source_metrics = _risk_source_metrics(source_product)
        source_metrics.update(
            {
                "selected_band_risk_fraction": None if resolved_band is None else resolved_band.selected_risk_fraction,
                "selected_band_liquid_fraction": None if resolved_band is None else resolved_band.selected_liquid_fraction,
                "selected_band_mixed_fraction": None if resolved_band is None else resolved_band.selected_mixed_fraction,
                "selected_band_mean_risk_fraction": None if resolved_band is None else resolved_band.mean_risk_fraction,
            }
        )
        source_metrics.update(band_metadata)
        return FinalProductSummary(
            dataset_path=dataset_path,
            time_index=source_product.time_index,
            time_label=source_product.time_label,
            source_mode=render_view,
            render_view=render_view,
            source_phase=5,
            source_phase_label="approximate icing risk",
            source_product_kind="approximate proxy",
            map_field_kind=f"Phase 5 approximate-risk footprint ({resolved_band_name} band)",
            map_semantics=(
                "binary approximate-risk footprint rendered directly from Phase 5 "
                f"and conditioned on the selected {resolved_band_name} model-relative band"
            ),
            map_geographic_context="Cartopy PlateCarree map with Natural Earth borders and coastlines framing the selected WRF domain",
            **band_metadata,
            source_artifacts=source_artifacts_map,
            source_metrics=source_metrics,
        )

    if render_view == "heuristic-severity":
        if not isinstance(source_product, Phase6HeuristicSeverityProduct):
            raise ValueError("heuristic-severity final products must be built from the phase-6 severity product.")
        source_metrics = _severity_source_metrics(source_product)
        source_metrics.update(
            {
                "selected_band_risk_fraction": None if resolved_band is None else resolved_band.selected_risk_fraction,
                "selected_band_liquid_fraction": None if resolved_band is None else resolved_band.selected_liquid_fraction,
                "selected_band_mixed_fraction": None if resolved_band is None else resolved_band.selected_mixed_fraction,
                "selected_band_mean_risk_fraction": None if resolved_band is None else resolved_band.mean_risk_fraction,
            }
        )
        source_metrics.update(band_metadata)
        return FinalProductSummary(
            dataset_path=dataset_path,
            time_index=source_product.time_index,
            time_label=source_product.time_label,
            source_mode=render_view,
            render_view=render_view,
            source_phase=6,
            source_phase_label="heuristic severity",
            source_product_kind="heuristic proxy",
            map_field_kind=f"Spatial heuristic severity score ({resolved_band_name} band)",
            map_semantics=(
                "2D band-conditioned heuristic severity score per cell derived from Phase 5 risk/liquid overlap, "
                "mixed-phase presence, and coherence within the selected model-relative band"
            ),
            map_geographic_context="Cartopy PlateCarree map with Natural Earth borders and coastlines framing the selected WRF domain",
            **band_metadata,
            source_artifacts=source_artifacts_map,
            source_metrics=source_metrics,
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

    base_name = (
        f"{FINAL_PRODUCT_OUTPUT_PREFIX}_t{summary.time_index:03d}_"
        f"{_view_slug(summary.render_view)}_band_{_view_slug(summary.selected_band)}"
    )
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
