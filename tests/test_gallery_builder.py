from __future__ import annotations

import json
from collections import deque
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from app.services.gallery_builder import GalleryBuildError, build_gallery


def _write_image(path: Path, color: tuple[int, int, int]) -> None:
    image = Image.new("RGB", (8, 8), color=color)
    image.save(path)


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
        self.input_sizes: list[tuple[int, int]] = []

    def setInputSize(self, size: tuple[int, int]) -> None:  # noqa: N802
        self.input_sizes.append(size)

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
    def __init__(
        self,
        detector: object | None,
        embedder: object | None,
        *,
        ready: bool = True,
    ) -> None:
        self._detector = detector
        self._embedder = embedder
        self._ready = ready

    def load_models(self) -> None:
        return None

    def get_detector(self) -> object | None:
        return self._detector

    def get_embedder(self) -> object | None:
        return self._embedder

    def detector_state(self) -> str:
        return "loaded" if self._ready and self._detector is not None else "present_not_loaded"

    def embedder_state(self) -> str:
        return "loaded" if self._ready and self._embedder is not None else "present_not_loaded"


def _identity_file(tmp_path: Path) -> Path:
    identity_file = tmp_path / "identity.txt"
    identity_file.write_text(
        "\n".join(
            [
                "one_face.jpg 2880",
                "no_face.jpg 2937",
                "invalid.jpg 8692",
                "multi_face.jpg 9001",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return identity_file


def _images_dir(tmp_path: Path) -> Path:
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    _write_image(images_dir / "one_face.jpg", (255, 0, 0))
    _write_image(images_dir / "no_face.jpg", (0, 255, 0))
    (images_dir / "invalid.jpg").write_text("not an image", encoding="utf-8")
    _write_image(images_dir / "multi_face.jpg", (0, 0, 255))
    return images_dir


def test_gallery_builder_writes_expected_artifacts(tmp_path: Path) -> None:
    images_dir = _images_dir(tmp_path)
    identity_file = _identity_file(tmp_path)
    output_dir = tmp_path / "gallery"
    runtime = FakeRuntime(
        detector=FakeDetector(
            [
                np.array([_face_row(x=10, y=20, width=30, height=40, score=0.98)]),
                np.empty((0, 15), dtype=np.float32),
                np.array(
                    [
                        _face_row(x=1, y=2, width=3, height=4, score=0.55),
                        _face_row(x=5, y=6, width=7, height=8, score=0.91),
                    ]
                ),
            ]
        ),
        embedder=FakeEmbedder(
            [
                np.arange(4, dtype=np.float32),
                np.arange(4, dtype=np.float32) + 10,
            ]
        ),
    )

    result = build_gallery(
        images_dir=images_dir,
        identity_file=identity_file,
        output_dir=output_dir,
        gallery_version="sample-gallery-v1",
        runtime=runtime,
    )

    assert result.item_count == 2
    assert result.identity_count == 2
    assert result.embeddings_path.is_file()
    assert result.metadata_path.is_file()
    assert result.manifest_path.is_file()
    assert result.report_path.is_file()

    embeddings = np.load(result.embeddings_path)
    assert embeddings.shape == (2, 4)

    metadata_lines = result.metadata_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(metadata_lines) == 2
    metadata_rows = [json.loads(line) for line in metadata_lines]
    assert metadata_rows[0]["celeba_identity_id"] == "2880"
    assert metadata_rows[0]["warnings"] == []
    assert metadata_rows[1]["warnings"] == ["multiple_faces_used_best"]
    assert metadata_rows[1]["face_box"] == [5, 6, 7, 8]
    assert "embedding" not in metadata_rows[0]

    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["gallery_version"] == "sample-gallery-v1"
    assert manifest["item_count"] == 2
    assert manifest["identity_count"] == 2
    assert manifest["embedding_dim"] == 4
    assert manifest["source"]["dataset"] == "CelebA-like local sample"

    report = json.loads(result.report_path.read_text(encoding="utf-8"))
    assert report["attempted"] == 4
    assert report["succeeded"] == 2
    assert report["skipped"] == 2
    assert report["skip_reasons"]["no_face"] == 1
    assert report["skip_reasons"]["decode_error"] == 1
    assert report["warnings"]["multiple_faces_used_best"] == 1


def test_gallery_builder_fails_when_runtime_not_ready(tmp_path: Path) -> None:
    images_dir = _images_dir(tmp_path)
    identity_file = _identity_file(tmp_path)
    runtime = FakeRuntime(detector=None, embedder=None, ready=False)

    with pytest.raises(GalleryBuildError, match="YuNet and SFace models must be loaded"):
        build_gallery(
            images_dir=images_dir,
            identity_file=identity_file,
            output_dir=tmp_path / "gallery",
            gallery_version="sample-gallery-v1",
            runtime=runtime,
        )


def test_gallery_builder_does_not_write_raw_embeddings(tmp_path: Path) -> None:
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    _write_image(images_dir / "one_face.jpg", (255, 0, 0))
    identity_file = tmp_path / "identity.txt"
    identity_file.write_text("one_face.jpg 2880\n", encoding="utf-8")
    runtime = FakeRuntime(
        detector=FakeDetector([np.array([_face_row(x=10, y=20, width=30, height=40, score=0.98)])]),
        embedder=FakeEmbedder([np.arange(4, dtype=np.float32)]),
    )

    result = build_gallery(
        images_dir=images_dir,
        identity_file=identity_file,
        output_dir=tmp_path / "gallery",
        gallery_version="sample-gallery-v1",
        runtime=runtime,
    )

    metadata = result.metadata_path.read_text(encoding="utf-8")
    report = result.report_path.read_text(encoding="utf-8")
    assert "0.0" not in metadata
    assert "embedding" not in metadata
    assert "vector" not in report
    assert "embedding_vector" not in report
