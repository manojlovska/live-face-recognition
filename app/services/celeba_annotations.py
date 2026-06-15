from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class CelebaAnnotationError(Exception):
    def __init__(self, message: str, code: str) -> None:
        super().__init__(message)
        self.message = message
        self.code = code


@dataclass(slots=True)
class CelebAIdentityAnnotation:
    image_filename: str
    identity_id: str


@dataclass(slots=True)
class CelebAPartitionAnnotation:
    image_filename: str
    partition: str


_PARTITION_LABELS = {
    "0": "train",
    "1": "val",
    "2": "test",
}


def load_celeba_identity_annotations(path: str | Path) -> list[CelebAIdentityAnnotation]:
    annotation_path = Path(path)
    if not annotation_path.is_file():
        raise CelebaAnnotationError(
            message="Identity annotation file does not exist.",
            code="identity_file_missing",
        )

    annotations: list[CelebAIdentityAnnotation] = []
    with annotation_path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split()
            if len(parts) != 2:
                raise CelebaAnnotationError(
                    message=(
                        "Identity annotation file must contain image filename and identity ID."
                        f" Invalid line {line_number}."
                    ),
                    code="identity_file_invalid",
                )

            image_filename, identity_id = parts
            annotations.append(
                CelebAIdentityAnnotation(
                    image_filename=image_filename,
                    identity_id=identity_id,
                )
            )

    if not annotations:
        raise CelebaAnnotationError(
            message="Identity annotation file is empty.",
            code="identity_file_empty",
        )

    return annotations


def load_celeba_partition_annotations(path: str | Path) -> list[CelebAPartitionAnnotation]:
    partition_path = Path(path)
    if not partition_path.is_file():
        raise CelebaAnnotationError(
            message="Partition annotation file does not exist.",
            code="partition_file_missing",
        )

    annotations: list[CelebAPartitionAnnotation] = []
    with partition_path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split()
            if len(parts) != 2:
                raise CelebaAnnotationError(
                    message=(
                        "Partition annotation file must contain image filename and partition ID."
                        f" Invalid line {line_number}."
                    ),
                    code="partition_file_invalid",
                )

            image_filename, partition_id = parts
            partition = _PARTITION_LABELS.get(partition_id)
            if partition is None:
                raise CelebaAnnotationError(
                    message=(
                        "Partition annotation file contains an unknown partition value."
                        f" Invalid line {line_number}."
                    ),
                    code="partition_file_invalid",
                )
            annotations.append(
                CelebAPartitionAnnotation(
                    image_filename=image_filename,
                    partition=partition,
                )
            )

    if not annotations:
        raise CelebaAnnotationError(
            message="Partition annotation file is empty.",
            code="partition_file_empty",
        )

    return annotations
