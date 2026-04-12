from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import DEFAULT_DATASET_NAME, DEFAULT_OUTPUT_DIR_NAME
from .dataset import DatasetValidationError, assert_valid, open_dataset, validate_dataset
from .phase2 import build_phase2_liquid_product, write_phase2_outputs
from .phase5 import build_phase5_approximate_risk_product, write_phase5_outputs
from .phase6 import build_phase6_heuristic_severity_product, write_phase6_outputs
from .summary import build_phase1_summary, write_phase1_outputs


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_dataset_path() -> Path:
    return _repo_root() / DEFAULT_DATASET_NAME


def _default_output_dir() -> Path:
    return _repo_root() / DEFAULT_OUTPUT_DIR_NAME


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pipeline reproducible del proyecto de riesgo de engelamiento.")
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

        if not validation.is_valid:
            print(validation.to_markdown(), file=sys.stderr)
            try:
                assert_valid(validation)
            except DatasetValidationError as exc:
                print(str(exc), file=sys.stderr)
                print(f"Validation artifacts written to: {markdown_path}", file=sys.stderr)
                print(f"Validation artifacts written to: {json_path}", file=sys.stderr)
                return 1

        try:
            phase2_product = build_phase2_liquid_product(dataset, args.dataset, time_index=args.time_index)
            phase2_markdown_path, phase2_json_path, phase2_netcdf_path, phase2_png_path = write_phase2_outputs(
                phase2_product,
                args.output_dir,
            )
            phase5_product = build_phase5_approximate_risk_product(dataset, args.dataset, time_index=args.time_index)
            phase5_markdown_path, phase5_json_path, phase5_netcdf_path, phase5_png_path = write_phase5_outputs(
                phase5_product,
                args.output_dir,
            )
            phase6_product = build_phase6_heuristic_severity_product(dataset, args.dataset, time_index=args.time_index)
            phase6_markdown_path, phase6_json_path, phase6_netcdf_path, phase6_png_path = write_phase6_outputs(
                phase6_product,
                args.output_dir,
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
    print(phase2_product.to_markdown(
        {
            "markdown": phase2_markdown_path,
            "json": phase2_json_path,
            "netcdf": phase2_netcdf_path,
            "png": phase2_png_path,
        }
    ))
    print()
    print(f"Markdown summary written to: {phase2_markdown_path}")
    print(f"JSON summary written to: {phase2_json_path}")
    print(f"NetCDF mask written to: {phase2_netcdf_path}")
    print(f"PNG mask written to: {phase2_png_path}")
    print()
    print(phase5_product.to_markdown(
        {
            "markdown": phase5_markdown_path,
            "json": phase5_json_path,
            "netcdf": phase5_netcdf_path,
            "png": phase5_png_path,
        }
    ))
    print()
    print(f"Markdown summary written to: {phase5_markdown_path}")
    print(f"JSON summary written to: {phase5_json_path}")
    print(f"NetCDF approximate-risk proxy written to: {phase5_netcdf_path}")
    print(f"PNG risk product written to: {phase5_png_path}")
    print()
    print(phase6_product.to_markdown(
        {
            "markdown": phase6_markdown_path,
            "json": phase6_json_path,
            "netcdf": phase6_netcdf_path,
            "png": phase6_png_path,
        },
        phase_number=6,
    ))
    print()
    print(f"Markdown summary written to: {phase6_markdown_path}")
    print(f"JSON summary written to: {phase6_json_path}")
    print(f"NetCDF heuristic severity product written to: {phase6_netcdf_path}")
    print(f"PNG heuristic severity product written to: {phase6_png_path}")
    return 0
