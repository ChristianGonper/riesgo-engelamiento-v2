from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import (
    DEFAULT_DATASET_NAME,
    DEFAULT_OUTPUT_DIR_NAME,
    FINAL_PRODUCT_RENDER_VIEWS,
    FINAL_PRODUCT_VERTICAL_BAND_CHOICES,
)
from .dataset import (
    DatasetValidationError,
    assert_valid,
    open_dataset,
    validate_dataset,
)
from .final_product import (
    build_final_product_summary,
    build_highlighted_times_summary,
    detect_dataset_presentation_capabilities,
    write_final_product_outputs,
    write_highlighted_times_outputs,
)
from .phase2 import build_phase2_liquid_product, write_phase2_outputs
from .phase5 import build_phase5_approximate_risk_product, write_phase5_outputs
from .phase6 import build_phase6_heuristic_severity_product, write_phase6_outputs
from .route_profile import (
    build_route_icing_profile_product,
    write_route_icing_profile_outputs,
)
from .summary import build_phase1_summary, write_phase1_outputs


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_dataset_path() -> Path:
    return _repo_root() / DEFAULT_DATASET_NAME


def _default_output_dir() -> Path:
    return _repo_root() / DEFAULT_OUTPUT_DIR_NAME


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pipeline reproducible del proyecto de riesgo de engelamiento."
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=_default_dataset_path(),
        help="Ruta al archivo WRF a validar.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_default_output_dir(),
        help="Directorio donde se escriben los artefactos reproducibles.",
    )
    parser.add_argument(
        "--time-index",
        type=int,
        default=0,
        help="Indice de tiempo a usar para las fases 2, 5 y 6.",
    )
    final_product_group = parser.add_mutually_exclusive_group()
    final_product_group.add_argument(
        "--final-deliverable",
        action="store_true",
        help="Genera el entregable final canonico para un tiempo seleccionado.",
    )
    final_product_group.add_argument(
        "--final-product",
        action="store_true",
        help="Alias legado del entregable final canonico; mantiene el prefijo historico de producto final.",
    )
    parser.add_argument(
        "--final-product-view",
        choices=FINAL_PRODUCT_RENDER_VIEWS,
        default="heuristic-severity",
        help="Vista diagnostica usada para el artefacto final de presentacion.",
    )
    parser.add_argument(
        "--final-product-band",
        choices=FINAL_PRODUCT_VERTICAL_BAND_CHOICES,
        default="dominant",
        help="Banda vertical relativa usada en el artefacto final; 'dominant' usa la banda dominante del tiempo seleccionado.",
    )
    parser.add_argument(
        "--final-product-highlighted-times",
        type=int,
        nargs="+",
        default=None,
        help="Indices de tiempo destacados para el comparativo compacto; si se omite, se puede usar la seleccion automatica con --final-product-highlighted-count.",
    )
    parser.add_argument(
        "--final-product-highlighted-count",
        type=int,
        default=0,
        help="Numero de tiempos destacados a seleccionar automaticamente cuando no se pasan indices explicitos. 0 desactiva el comparativo.",
    )
    parser.add_argument(
        "--route-profile",
        action="store_true",
        help="Genera un perfil de engelamiento en ruta (distancia-km vs niveles eta).",
    )
    parser.add_argument(
        "--route-start-lat",
        type=float,
        default=None,
        help="Latitud de inicio de la ruta.",
    )
    parser.add_argument(
        "--route-start-lon",
        type=float,
        default=None,
        help="Longitud de inicio de la ruta.",
    )
    parser.add_argument(
        "--route-end-lat", type=float, default=None, help="Latitud final de la ruta."
    )
    parser.add_argument(
        "--route-end-lon", type=float, default=None, help="Longitud final de la ruta."
    )
    parser.add_argument(
        "--route-points",
        type=int,
        default=200,
        help="Numero de puntos de muestreo sobre la ruta para el perfil.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.dataset.exists():
        print(f"Dataset not found: {args.dataset}", file=sys.stderr)
        return 1

    with open_dataset(args.dataset) as dataset:
        validation = validate_dataset(dataset, source=args.dataset)
        summary = build_phase1_summary(dataset, validation, args.dataset)
        markdown_path, json_path = write_phase1_outputs(summary, args.output_dir)
        presentation_capabilities = detect_dataset_presentation_capabilities(dataset)

        if not validation.is_valid:
            print(validation.to_markdown(), file=sys.stderr)
            try:
                assert_valid(validation)
            except DatasetValidationError as exc:
                print(str(exc), file=sys.stderr)
                print(
                    f"Validation artifacts written to: {markdown_path}", file=sys.stderr
                )
                print(f"Validation artifacts written to: {json_path}", file=sys.stderr)
                return 1

        try:
            phase2_product = build_phase2_liquid_product(
                dataset, args.dataset, time_index=args.time_index
            )
            (
                phase2_markdown_path,
                phase2_json_path,
                phase2_netcdf_path,
                phase2_png_path,
            ) = write_phase2_outputs(
                phase2_product,
                args.output_dir,
            )
            phase5_product = build_phase5_approximate_risk_product(
                dataset, args.dataset, time_index=args.time_index
            )
            (
                phase5_markdown_path,
                phase5_json_path,
                phase5_netcdf_path,
                phase5_png_path,
            ) = write_phase5_outputs(
                phase5_product,
                args.output_dir,
            )
            phase6_product = build_phase6_heuristic_severity_product(
                dataset, args.dataset, time_index=args.time_index
            )
            (
                phase6_markdown_path,
                phase6_json_path,
                phase6_netcdf_path,
                phase6_png_path,
            ) = write_phase6_outputs(
                phase6_product,
                args.output_dir,
            )
            final_product_summary = None
            final_product_markdown_path = None
            final_product_json_path = None
            final_product_png_path = None
            final_product_source_products = None
            highlighted_times_markdown_path = None
            highlighted_times_json_path = None
            highlighted_times_png_path = None
            highlighted_times_summary = None
            route_profile_product = None
            route_profile_markdown_path = None
            route_profile_json_path = None
            route_profile_png_path = None
            if args.final_deliverable or args.final_product:
                delivery_mode = "canonical" if args.final_deliverable else "legacy"
                if args.final_product_view == "approximate-risk":
                    final_product_summary = build_final_product_summary(
                        phase5_product,
                        args.dataset,
                        render_view=args.final_product_view,
                        selected_band=args.final_product_band,
                        delivery_mode=delivery_mode,
                        severity_product=phase6_product,
                        presentation_capabilities=presentation_capabilities,
                        source_artifacts={
                            "phase5_markdown": phase5_markdown_path,
                            "phase5_json": phase5_json_path,
                            "phase5_netcdf": phase5_netcdf_path,
                            "phase5_png": phase5_png_path,
                        },
                    )
                    final_product_source_products = {
                        "risk_product": phase5_product,
                        "severity_product": None,
                    }
                else:
                    final_product_summary = build_final_product_summary(
                        phase6_product,
                        args.dataset,
                        render_view=args.final_product_view,
                        selected_band=args.final_product_band,
                        delivery_mode=delivery_mode,
                        severity_product=phase6_product,
                        presentation_capabilities=presentation_capabilities,
                        source_artifacts={
                            "phase6_markdown": phase6_markdown_path,
                            "phase6_json": phase6_json_path,
                            "phase6_netcdf": phase6_netcdf_path,
                            "phase6_png": phase6_png_path,
                            "phase5_markdown": phase5_markdown_path,
                            "phase5_json": phase5_json_path,
                            "phase5_netcdf": phase5_netcdf_path,
                            "phase5_png": phase5_png_path,
                        },
                    )
                    final_product_source_products = {
                        "risk_product": phase5_product,
                        "severity_product": phase6_product,
                    }
                (
                    final_product_markdown_path,
                    final_product_json_path,
                    final_product_png_path,
                ) = write_final_product_outputs(
                    final_product_summary,
                    args.output_dir,
                    risk_product=final_product_source_products["risk_product"],
                    severity_product=final_product_source_products["severity_product"],
                    source_dataset=dataset,
                )
                if (
                    args.final_product_highlighted_times is not None
                    or args.final_product_highlighted_count > 0
                ):
                    highlighted_times_summary = build_highlighted_times_summary(
                        phase6_product,
                        args.dataset,
                        source_mode=args.final_product_view,
                        reference_time_index=args.time_index,
                        highlighted_times=args.final_product_highlighted_times,
                        highlighted_time_count=args.final_product_highlighted_count,
                        presentation_capabilities=presentation_capabilities,
                        source_artifacts={
                            "phase5_markdown": phase5_markdown_path,
                            "phase5_json": phase5_json_path,
                            "phase5_netcdf": phase5_netcdf_path,
                            "phase5_png": phase5_png_path,
                            "phase6_markdown": phase6_markdown_path,
                            "phase6_json": phase6_json_path,
                            "phase6_netcdf": phase6_netcdf_path,
                            "phase6_png": phase6_png_path,
                        },
                    )
                    (
                        highlighted_times_markdown_path,
                        highlighted_times_json_path,
                        highlighted_times_png_path,
                    ) = write_highlighted_times_outputs(
                        highlighted_times_summary,
                        args.output_dir,
                    )
            if args.route_profile:
                required_route_args = (
                    args.route_start_lat,
                    args.route_start_lon,
                    args.route_end_lat,
                    args.route_end_lon,
                )
                if any(value is None for value in required_route_args):
                    raise ValueError(
                        "--route-profile requires --route-start-lat, --route-start-lon, --route-end-lat and --route-end-lon."
                    )
                route_profile_product = build_route_icing_profile_product(
                    dataset,
                    args.dataset,
                    time_index=args.time_index,
                    route_start_lat=float(args.route_start_lat),
                    route_start_lon=float(args.route_start_lon),
                    route_end_lat=float(args.route_end_lat),
                    route_end_lon=float(args.route_end_lon),
                    route_points=int(args.route_points),
                )
                (
                    route_profile_markdown_path,
                    route_profile_json_path,
                    route_profile_png_path,
                ) = write_route_icing_profile_outputs(
                    route_profile_product, args.output_dir
                )
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1

    print()
    print(summary.to_markdown())
    print()
    print(f"Markdown summary written to: {markdown_path}")
    print(f"JSON summary written to: {json_path}")
    print()
    print(
        phase2_product.to_markdown(
            {
                "markdown": phase2_markdown_path,
                "json": phase2_json_path,
                "netcdf": phase2_netcdf_path,
                "png": phase2_png_path,
            }
        )
    )
    print()
    print(f"Markdown summary written to: {phase2_markdown_path}")
    print(f"JSON summary written to: {phase2_json_path}")
    print(f"NetCDF mask written to: {phase2_netcdf_path}")
    print(f"PNG mask written to: {phase2_png_path}")
    print()
    print(
        phase5_product.to_markdown(
            {
                "markdown": phase5_markdown_path,
                "json": phase5_json_path,
                "netcdf": phase5_netcdf_path,
                "png": phase5_png_path,
            }
        )
    )
    print()
    print(f"Markdown summary written to: {phase5_markdown_path}")
    print(f"JSON summary written to: {phase5_json_path}")
    print(f"NetCDF approximate-risk proxy written to: {phase5_netcdf_path}")
    print(f"PNG risk product written to: {phase5_png_path}")
    print()
    print(
        phase6_product.to_markdown(
            {
                "markdown": phase6_markdown_path,
                "json": phase6_json_path,
                "netcdf": phase6_netcdf_path,
                "png": phase6_png_path,
            },
            phase_number=6,
        )
    )
    print()
    print(f"Markdown summary written to: {phase6_markdown_path}")
    print(f"JSON summary written to: {phase6_json_path}")
    print(f"NetCDF heuristic severity product written to: {phase6_netcdf_path}")
    print(f"PNG heuristic severity product written to: {phase6_png_path}")
    if final_product_summary is not None:
        assert final_product_markdown_path is not None
        assert final_product_json_path is not None
        assert final_product_png_path is not None
        final_product_outputs: dict[str, Path] = {
            "markdown": final_product_markdown_path,
            "json": final_product_json_path,
            "png": final_product_png_path,
        }
        print()
        print(final_product_summary.to_markdown(final_product_outputs))
        print()
        print(f"Markdown summary written to: {final_product_markdown_path}")
        print(f"JSON summary written to: {final_product_json_path}")
        print(
            f"PNG {final_product_summary.delivery_label} written to: {final_product_png_path}"
        )
    if highlighted_times_summary is not None:
        assert highlighted_times_markdown_path is not None
        assert highlighted_times_json_path is not None
        assert highlighted_times_png_path is not None
        highlighted_times_outputs: dict[str, Path] = {
            "markdown": highlighted_times_markdown_path,
            "json": highlighted_times_json_path,
            "png": highlighted_times_png_path,
        }
        print()
        print(highlighted_times_summary.to_markdown(highlighted_times_outputs))
        print()
        print(f"Markdown summary written to: {highlighted_times_markdown_path}")
        print(f"JSON summary written to: {highlighted_times_json_path}")
        print(
            f"PNG highlighted-times comparison written to: {highlighted_times_png_path}"
        )
    if route_profile_product is not None:
        assert route_profile_markdown_path is not None
        assert route_profile_json_path is not None
        assert route_profile_png_path is not None
        route_profile_outputs: dict[str, Path] = {
            "markdown": route_profile_markdown_path,
            "json": route_profile_json_path,
            "png": route_profile_png_path,
        }
        print()
        print(route_profile_product.to_markdown(route_profile_outputs))
        print()
        print(f"Markdown summary written to: {route_profile_markdown_path}")
        print(f"JSON summary written to: {route_profile_json_path}")
        print(f"PNG route profile written to: {route_profile_png_path}")
    return 0
