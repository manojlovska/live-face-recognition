from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from scripts.build_gallery import main


class ScriptFakeDetector:
    def __init__(self) -> None:
        self._responses = [
            np.array(
                [
                    [
                        10,
                        20,
                        30,
                        40,
                        11,
                        21,
                        12,
                        21,
                        11,
                        22,
                        11,
                        23,
                        12,
                        23,
                        0.99,
                    ]
                ],
                dtype=np.float32,
            )
        ]

    def setInputSize(self, _size: tuple[int, int]) -> None:  # noqa: N802
        return None

    def detect(self, _bgr_image: np.ndarray) -> np.ndarray:
        return self._responses.pop(0) if self._responses else np.empty((0, 15), dtype=np.float32)


class ScriptFakeEmbedder:
    def alignCrop(self, bgr_image: np.ndarray, _detection_row: np.ndarray) -> np.ndarray:  # noqa: N802
        return bgr_image

    def feature(self, _aligned_face: np.ndarray) -> np.ndarray:
        return np.arange(4, dtype=np.float32)


class ScriptFakeRuntime:
    def load_models(self) -> None:
        return None

    def get_detector(self) -> object:
        return ScriptFakeDetector()

    def get_embedder(self) -> object:
        return ScriptFakeEmbedder()

    def detector_state(self) -> str:
        return "loaded"

    def embedder_state(self) -> str:
        return "loaded"


def _write_sample_image(path: Path) -> None:
    Image.new("RGB", (8, 8), color=(255, 0, 0)).save(path)


def test_gallery_builder_script_dry_run_and_success(tmp_path: Path) -> None:
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    _write_sample_image(images_dir / "000001.jpg")
    identity_file = tmp_path / "identity.txt"
    identity_file.write_text("000001.jpg 2880\n", encoding="utf-8")
    output_dir = tmp_path / "gallery"

    exit_code = main(
        [
            "--images-dir",
            str(images_dir),
            "--identity-file",
            str(identity_file),
            "--output-dir",
            str(output_dir),
            "--gallery-version",
            "sample-gallery-v1",
            "--dry-run",
        ],
        runtime_factory=lambda _settings: ScriptFakeRuntime(),
    )

    assert exit_code == 0
    assert not output_dir.exists()

    exit_code = main(
        [
            "--images-dir",
            str(images_dir),
            "--identity-file",
            str(identity_file),
            "--output-dir",
            str(output_dir),
            "--gallery-version",
            "sample-gallery-v1",
        ],
        runtime_factory=lambda _settings: ScriptFakeRuntime(),
    )

    assert exit_code == 0
    assert (output_dir / "gallery_embeddings.npy").is_file()
    assert (output_dir / "gallery_metadata.jsonl").is_file()
    assert (output_dir / "gallery_manifest.json").is_file()
    assert (output_dir / "gallery_build_report.json").is_file()


def test_gallery_builder_script_rejects_missing_input_dir(tmp_path: Path) -> None:
    identity_file = tmp_path / "identity.txt"
    identity_file.write_text("000001.jpg 2880\n", encoding="utf-8")

    exit_code = main(
        [
            "--images-dir",
            str(tmp_path / "missing"),
            "--identity-file",
            str(identity_file),
            "--output-dir",
            str(tmp_path / "gallery"),
            "--gallery-version",
            "sample-gallery-v1",
        ],
        runtime_factory=lambda _settings: ScriptFakeRuntime(),
    )

    assert exit_code == 1


def test_gallery_builder_script_rejects_existing_output_without_overwrite(tmp_path: Path) -> None:
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    _write_sample_image(images_dir / "000001.jpg")
    identity_file = tmp_path / "identity.txt"
    identity_file.write_text("000001.jpg 2880\n", encoding="utf-8")
    output_dir = tmp_path / "gallery"
    output_dir.mkdir()
    (output_dir / "gallery_embeddings.npy").write_bytes(b"existing")

    exit_code = main(
        [
            "--images-dir",
            str(images_dir),
            "--identity-file",
            str(identity_file),
            "--output-dir",
            str(output_dir),
            "--gallery-version",
            "sample-gallery-v1",
        ],
        runtime_factory=lambda _settings: ScriptFakeRuntime(),
    )

    assert exit_code == 1
