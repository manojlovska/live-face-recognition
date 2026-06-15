from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class CelebaLayoutError(Exception):
    def __init__(self, message: str, code: str) -> None:
        super().__init__(message)
        self.message = message
        self.code = code


@dataclass(slots=True)
class CelebaLayout:
    celeba_root: Path
    images_dir: Path
    identity_file: Path
    partition_file: Path | None
    layout_kind: str


def discover_celeba_layout(
    celeba_root: str | Path,
    *,
    images_dir: str | Path | None = None,
    identity_file: str | Path | None = None,
    partition_file: str | Path | None = None,
) -> CelebaLayout:
    root = Path(celeba_root)
    if not root.is_dir():
        raise CelebaLayoutError(
            message="CelebA root directory does not exist.",
            code="celeba_root_missing",
        )

    discovered_images_dir, layout_kind = _discover_images_dir(root)
    discovered_identity_file = _discover_named_file(root, "identity_CelebA.txt")
    discovered_partition_file = _discover_named_file(root, "list_eval_partition.txt")
    if discovered_identity_file is None:
        raise CelebaLayoutError(
            message="Could not find identity_CelebA.txt under the CelebA root.",
            code="celeba_identity_missing",
        )

    explicit_images_dir = _resolve_optional_path(images_dir)
    explicit_identity_file = _resolve_optional_path(identity_file)
    explicit_partition_file = _resolve_optional_path(partition_file)

    if (
        explicit_images_dir is not None
        and explicit_images_dir.resolve() != discovered_images_dir.resolve()
    ):
        raise CelebaLayoutError(
            message="Explicit images directory does not match the discovered CelebA layout.",
            code="celeba_layout_mismatch",
        )
    if (
        explicit_identity_file is not None
        and explicit_identity_file.resolve() != discovered_identity_file.resolve()
    ):
        raise CelebaLayoutError(
            message="Explicit identity file does not match the discovered CelebA layout.",
            code="celeba_layout_mismatch",
        )
    if explicit_partition_file is not None:
        if (
            discovered_partition_file is not None
            and explicit_partition_file.resolve() != discovered_partition_file.resolve()
        ):
            raise CelebaLayoutError(
                message="Explicit partition file does not match the discovered CelebA layout.",
                code="celeba_layout_mismatch",
            )
        discovered_partition_file = explicit_partition_file

    return CelebaLayout(
        celeba_root=root,
        images_dir=explicit_images_dir or discovered_images_dir,
        identity_file=explicit_identity_file or discovered_identity_file,
        partition_file=discovered_partition_file,
        layout_kind=layout_kind,
    )


def _discover_images_dir(root: Path) -> tuple[Path, str]:
    outer = root / "img_align_celeba"
    nested = outer / "img_align_celeba"
    if outer.is_dir() and _contains_direct_image_files(outer):
        return outer, "img_align_celeba"
    if nested.is_dir() and _contains_direct_image_files(nested):
        return nested, "nested_img_align_celeba"
    if outer.is_dir():
        return outer, "img_align_celeba"
    raise CelebaLayoutError(
        message="Could not find an img_align_celeba directory under the CelebA root.",
        code="celeba_images_missing",
    )


def _discover_named_file(root: Path, filename: str) -> Path | None:
    candidates = sorted(root.rglob(filename), key=lambda path: (len(path.parts), str(path)))
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _contains_direct_image_files(directory: Path) -> bool:
    supported_suffixes = {".jpg", ".jpeg", ".png", ".webp"}
    return any(
        child.is_file() and child.suffix.lower() in supported_suffixes
        for child in directory.iterdir()
    )


def _resolve_optional_path(path: str | Path | None) -> Path | None:
    if path is None:
        return None
    return Path(path)
