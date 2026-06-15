from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path

from app.config import Settings, get_settings
from app.services.gallery_builder import GalleryBuildError, build_gallery
from app.services.model_runtime import ModelRuntime


def _build_runtime(settings: Settings) -> ModelRuntime:
    return ModelRuntime(settings)


def _parse_include_partitions(values: list[str] | None) -> list[str] | None:
    if values is None:
        return None
    partitions: list[str] = []
    for value in values:
        for item in value.split(","):
            normalized = item.strip()
            if normalized:
                partitions.append(normalized)
    return partitions or None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a local face gallery artifact.")
    parser.add_argument("--celeba-root")
    parser.add_argument("--images-dir")
    parser.add_argument("--identity-file")
    parser.add_argument("--partition-file")
    parser.add_argument("--include-partitions", nargs="*")
    parser.add_argument("--start-after")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--gallery-version", required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--fail-on-empty", action="store_true")
    parser.add_argument("--min-det-score", type=float, default=0.0)
    return parser


def main(
    argv: list[str] | None = None,
    *,
    runtime_factory: Callable[[Settings], object] | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.celeba_root is None and (args.images_dir is None or args.identity_file is None):
        print(
            "either --celeba-root or both --images-dir and --identity-file are required",
            file=sys.stderr,
        )
        return 1
    settings = get_settings()
    runtime = runtime_factory(settings) if runtime_factory is not None else _build_runtime(settings)

    try:
        result = build_gallery(
            celeba_root=Path(args.celeba_root) if args.celeba_root is not None else None,
            images_dir=Path(args.images_dir) if args.images_dir is not None else None,
            identity_file=Path(args.identity_file) if args.identity_file is not None else None,
            partition_file=(Path(args.partition_file) if args.partition_file is not None else None),
            include_partitions=_parse_include_partitions(args.include_partitions),
            start_after=args.start_after,
            output_dir=Path(args.output_dir),
            gallery_version=args.gallery_version,
            runtime=runtime,
            limit=args.limit,
            overwrite=args.overwrite,
            dry_run=args.dry_run,
            fail_on_empty=args.fail_on_empty,
            min_det_score=args.min_det_score,
        )
    except GalleryBuildError as exc:
        print(f"{exc.code}: {exc.message}", file=sys.stderr)
        return 1

    print(json.dumps(result.summary(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
