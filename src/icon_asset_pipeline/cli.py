from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from icon_asset_pipeline.generation import write_generation_brief
from icon_asset_pipeline.models import PipelineConfig
from icon_asset_pipeline.pipeline import run_directory_pipeline, run_extract_pipeline


def _sizes(value: str) -> tuple[int, ...]:
    try:
        sizes = tuple(int(part.strip()) for part in value.split(",") if part.strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--sizes must be comma-separated integers") from exc
    if not sizes:
        raise argparse.ArgumentTypeError("--sizes cannot be empty")
    return sizes


def _config(args: argparse.Namespace) -> PipelineConfig:
    return PipelineConfig(
        sizes=args.sizes,
        padding_ratio=args.padding,
        min_area_ratio=args.min_area_ratio,
        expected_count=getattr(args, "expected_count", None),
        prompt=getattr(args, "prompt", None),
        names_file=Path(args.names_file) if getattr(args, "names_file", None) else None,
        webp=not getattr(args, "no_webp", False),
        sprite=not getattr(args, "no_sprite", False),
        zip_output=not getattr(args, "no_zip", False),
        svg=getattr(args, "svg", False),
        repair=getattr(args, "repair", False),
        duplicate_threshold=getattr(args, "duplicate_threshold", 7),
        category=getattr(args, "category", None),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate briefs, extract, normalize, and package production icon assets.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    brief = subparsers.add_parser("brief", help="Create a prompt brief for icon sheet generation.")
    brief.add_argument("--prompt", required=True)
    brief.add_argument("--output", required=True, type=Path)
    brief.add_argument("--count", type=int)

    def add_common(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--output", required=True, type=Path)
        subparser.add_argument("--sizes", type=_sizes, default=(128, 256, 512, 1024))
        subparser.add_argument("--padding", type=float, default=0.16)
        subparser.add_argument("--min-area-ratio", type=float, default=0.00018)
        subparser.add_argument("--prompt")
        subparser.add_argument("--names-file")
        subparser.add_argument("--category")
        subparser.add_argument("--duplicate-threshold", type=int, default=7)
        subparser.add_argument("--svg", action="store_true")
        subparser.add_argument("--repair", action="store_true")
        subparser.add_argument("--no-webp", action="store_true")
        subparser.add_argument("--no-sprite", action="store_true")
        subparser.add_argument("--no-zip", action="store_true")

    extract = subparsers.add_parser("extract", help="Extract icons from one source sheet and package them.")
    extract.add_argument("--input", required=True, type=Path)
    extract.add_argument("--expected-count", type=int)
    add_common(extract)

    repair = subparsers.add_parser("repair", help="Extract with conservative repair/cleanup enabled.")
    repair.add_argument("--input", required=True, type=Path)
    repair.add_argument("--expected-count", type=int)
    add_common(repair)

    normalize = subparsers.add_parser("normalize", help="Normalize and package a directory of individual icons.")
    normalize.add_argument("--input", required=True, type=Path)
    add_common(normalize)

    package = subparsers.add_parser("package", help="Package a directory of icons with optional normalization.")
    package.add_argument("--input", required=True, type=Path)
    package.add_argument("--preserve-size", action="store_true")
    add_common(package)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "brief":
        path = write_generation_brief(args.prompt, args.output, count=args.count)
        print(json.dumps({"generation_brief": str(path)}, indent=2))
        return 0

    config = _config(args)
    if args.command == "repair":
        config.repair = True

    if args.command in {"extract", "repair"}:
        result = run_extract_pipeline(args.input, args.output, config)
    elif args.command == "normalize":
        result = run_directory_pipeline(args.input, args.output, config, normalize=True)
    elif args.command == "package":
        result = run_directory_pipeline(args.input, args.output, config, normalize=not args.preserve_size)
    else:
        parser.error(f"Unknown command: {args.command}")
        return 2

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
