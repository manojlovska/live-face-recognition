from __future__ import annotations

import json
from collections import deque
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from app.services.gallery_builder import build_gallery


def _write_image(path: Path, color: tuple[int, int, int]) -> None:
    Image.new("RGB", (8, 8), color=color).save(path)


def _face_row(
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    score: float,
) -> np.ndarray:
    row = np.zeros(15, dtype=np.float32)
    row[0:4] = [x, y, width, height]
    row[4:14] = [x + 1, y + 1, x + 2, y + 1, x + 1.5, y + 2, x + 1, y + 3, x + 2, y + 3]
    row[14] = score
    return row


class FakeDetector:
    def __init__(self, responses: list[np.ndarray]) -> None:
        self._responses = deque(responses)

    def setInputSize(self, _size: tuple[int, int]) -> None:  # noqa: N802
        return None

    def detect(self, _bgr_image: np.ndarray) -> np.ndarray:
        if self._responses:
            return self._responses.popleft()
        return np.empty((0, 15), dtype=np.float32)


class FakeEmbedder:
    def __init__(self, vectors: list[np.ndarray]) -> None:
        self._vectors = deque(vectors)

    def alignCrop(self, bgr_image: np.ndarray, _detection_row: np.ndarray) -> np.ndarray:  # noqa: N802
        return bgr_image

    def feature(self, _aligned_face: np.ndarray) -> np.ndarray:
        if not self._vectors:
            raise RuntimeError("No more fake vectors.")
        return self._vectors.popleft()


class FakeRuntime:
    def __init__(self, detector: object | None, embedder: object | None) -> None:
        self._detector = detector
        self._embedder = embedder

    def load_models(self) -> None:
        return None

    def get_detector(self) -> object | None:
        return self._detector

    def get_embedder(self) -> object | None:
        return self._embedder

    def detector_state(self) -> str:
        return "loaded" if self._detector is not None else "present_not_loaded"

    def embedder_state(self) -> str:
        return "loaded" if self._embedder is not None else "present_not_loaded"


def _sample_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    _write_image(images_dir / "000001.jpg", (255, 0, 0))
    _write_image(images_dir / "000002.jpg", (0, 255, 0))
    _write_image(images_dir / "000003.jpg", (0, 0, 255))
    _write_image(images_dir / "000004.jpg", (255, 255, 0))

    identity_file = tmp_path / "identity.txt"
    identity_file.write_text(
        "\n".join(
            [
                "000001.jpg 2880",
                "000002.jpg 2937",
                "000003.jpg 8692",
                "000004.jpg 9001",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    partition_file = tmp_path / "list_eval_partition.txt"
    partition_file.write_text(
        "\n".join(
            [
                "000001.jpg 0",
                "000002.jpg 1",
                "000003.jpg 2",
                "000004.jpg 0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return images_dir, identity_file, partition_file


def test_gallery_builder_reports_quality_and_performance(tmp_path: Path) -> None:
    images_dir, identity_file, partition_file = _sample_inputs(tmp_path)
    output_dir = tmp_path / "gallery"
    runtime = FakeRuntime(
        detector=FakeDetector(
            [
                np.array(
                    [
                        _face_row(x=1, y=2, width=3, height=4, score=0.55),
                        _face_row(x=5, y=6, width=7, height=8, score=0.95),
                    ]
                ),
                np.array([_face_row(x=9, y=10, width=11, height=12, score=0.75)]),
            ]
        ),
        embedder=FakeEmbedder([np.arange(4, dtype=np.float32)]),
    )

    result = build_gallery(
        images_dir=images_dir,
        identity_file=identity_file,
        partition_file=partition_file,
        output_dir=output_dir,
        gallery_version="celeba-local-v1",
        runtime=runtime,
        include_partitions=["train", "val"],
        start_after="000001.jpg",
        limit=2,
        min_det_score=0.8,
    )

    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    report = json.loads(result.report_path.read_text(encoding="utf-8"))
    metadata_rows = [
        json.loads(line) for line in result.metadata_path.read_text(encoding="utf-8").splitlines()
    ]

    assert result.item_count == 1
    assert result.identity_count == 1
    assert manifest["gallery_scope"] == "sample"
    assert manifest["filters"]["limit"] == 2
    assert manifest["filters"]["include_partitions"] == ["train", "val"]
    assert manifest["filters"]["start_after"] == "000001.jpg"
    assert manifest["filters"]["min_detection_score"] == 0.8
    assert report["attempted"] == 2
    assert report["succeeded"] == 1
    assert report["skipped"] == 1
    assert report["skip_reasons"]["low_detection_score"] == 1
    assert report["warnings"]["multiple_faces_used_best"] == 1
    assert report["quality"]["success_rate"] == pytest.approx(0.5)
    assert report["quality"]["identity_count"] == 1
    assert report["quality"]["min_detection_score"] == pytest.approx(0.95)
    assert report["quality"]["mean_detection_score"] == pytest.approx(0.95)
    assert report["quality"]["median_detection_score"] == pytest.approx(0.95)
    assert report["performance"]["started_at"]
    assert report["performance"]["finished_at"]
    assert report["performance"]["duration_seconds"] >= 0.0
    assert metadata_rows[0]["split"] == "val"
    assert metadata_rows[0]["warnings"] == ["multiple_faces_used_best"]
    assert "embedding" not in report
