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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a local face gallery artifact.")
    parser.add_argument("--images-dir", required=True)
    parser.add_argument("--identity-file", required=True)
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
    settings = get_settings()
    runtime = runtime_factory(settings) if runtime_factory is not None else _build_runtime(settings)

    try:
        result = build_gallery(
            images_dir=Path(args.images_dir),
            identity_file=Path(args.identity_file),
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
