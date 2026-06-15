from __future__ import annotations

from pathlib import Path

import pytest

from app.services.celeba_annotations import (
    CelebaAnnotationError,
    load_celeba_partition_annotations,
)


def test_load_celeba_partition_annotations_parses_valid_file(tmp_path: Path) -> None:
    partition_file = tmp_path / "list_eval_partition.txt"
    partition_file.write_text(
        "\n".join(
            [
                "# comment",
                "",
                "000001.jpg 0",
                "000002.jpg 1",
                "000003.jpg 2",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    annotations = load_celeba_partition_annotations(partition_file)

    assert [annotation.image_filename for annotation in annotations] == [
        "000001.jpg",
        "000002.jpg",
        "000003.jpg",
    ]
    assert [annotation.partition for annotation in annotations] == ["train", "val", "test"]


def test_load_celeba_partition_annotations_rejects_malformed_line(tmp_path: Path) -> None:
    partition_file = tmp_path / "list_eval_partition.txt"
    partition_file.write_text("000001.jpg\n", encoding="utf-8")

    with pytest.raises(CelebaAnnotationError, match="Invalid line 1"):
        load_celeba_partition_annotations(partition_file)


def test_load_celeba_partition_annotations_rejects_unknown_partition_value(
    tmp_path: Path,
) -> None:
    partition_file = tmp_path / "list_eval_partition.txt"
    partition_file.write_text("000001.jpg 9\n", encoding="utf-8")

    with pytest.raises(CelebaAnnotationError, match="unknown partition value"):
        load_celeba_partition_annotations(partition_file)
