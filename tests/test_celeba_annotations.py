from __future__ import annotations

from pathlib import Path

import pytest

from app.services.celeba_annotations import (
    CelebaAnnotationError,
    load_celeba_identity_annotations,
)


def test_load_celeba_identity_annotations_parses_valid_file(tmp_path: Path) -> None:
    identity_file = tmp_path / "identity.txt"
    identity_file.write_text(
        "\n".join(
            [
                "# comment",
                "",
                "000001.jpg 2880",
                "000002.jpg 2937",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    annotations = load_celeba_identity_annotations(identity_file)

    assert [annotation.image_filename for annotation in annotations] == [
        "000001.jpg",
        "000002.jpg",
    ]
    assert [annotation.identity_id for annotation in annotations] == ["2880", "2937"]


def test_load_celeba_identity_annotations_rejects_malformed_line(tmp_path: Path) -> None:
    identity_file = tmp_path / "identity.txt"
    identity_file.write_text("000001.jpg\n", encoding="utf-8")

    with pytest.raises(CelebaAnnotationError, match="Invalid line 1"):
        load_celeba_identity_annotations(identity_file)


def test_load_celeba_identity_annotations_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(CelebaAnnotationError, match="does not exist"):
        load_celeba_identity_annotations(tmp_path / "missing.txt")
