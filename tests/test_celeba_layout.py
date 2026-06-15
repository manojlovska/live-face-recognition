from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from app.services.celeba_layout import CelebaLayoutError, discover_celeba_layout


def _write_image(path: Path) -> None:
    Image.new("RGB", (8, 8), color=(255, 0, 0)).save(path)


def test_discover_celeba_layout_finds_flat_img_align_directory(tmp_path: Path) -> None:
    celeba_root = tmp_path / "celeba"
    images_dir = celeba_root / "img_align_celeba"
    images_dir.mkdir(parents=True)
    _write_image(images_dir / "000001.jpg")
    (celeba_root / "identity_CelebA.txt").write_text("000001.jpg 2880\n", encoding="utf-8")

    layout = discover_celeba_layout(celeba_root)

    assert layout.images_dir == images_dir
    assert layout.identity_file == celeba_root / "identity_CelebA.txt"
    assert layout.partition_file is None


def test_discover_celeba_layout_finds_nested_img_align_directory(tmp_path: Path) -> None:
    celeba_root = tmp_path / "celeba"
    nested_dir = celeba_root / "img_align_celeba" / "img_align_celeba"
    nested_dir.mkdir(parents=True)
    _write_image(nested_dir / "000001.jpg")
    (celeba_root / "identity_CelebA.txt").write_text("000001.jpg 2880\n", encoding="utf-8")

    layout = discover_celeba_layout(celeba_root)

    assert layout.images_dir == nested_dir
    assert layout.layout_kind == "nested_img_align_celeba"


def test_discover_celeba_layout_rejects_missing_identity_file(tmp_path: Path) -> None:
    celeba_root = tmp_path / "celeba"
    images_dir = celeba_root / "img_align_celeba"
    images_dir.mkdir(parents=True)
    _write_image(images_dir / "000001.jpg")

    with pytest.raises(CelebaLayoutError) as excinfo:
        discover_celeba_layout(celeba_root)

    assert excinfo.value.code == "celeba_identity_missing"


def test_discover_celeba_layout_rejects_missing_image_directory(tmp_path: Path) -> None:
    celeba_root = tmp_path / "celeba"
    celeba_root.mkdir()
    (celeba_root / "identity_CelebA.txt").write_text("000001.jpg 2880\n", encoding="utf-8")

    with pytest.raises(CelebaLayoutError) as excinfo:
        discover_celeba_layout(celeba_root)

    assert excinfo.value.code == "celeba_images_missing"
