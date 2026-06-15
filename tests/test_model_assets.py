from __future__ import annotations

import hashlib

from app.config import Settings
from app.services.model_assets import (
    CHECKSUM_FILE_MISSING,
    CHECKSUM_MATCH,
    CHECKSUM_MISMATCH,
    CHECKSUM_MISSING_EXPECTED,
    MANIFEST_MISSING,
    ModelAssetManager,
    build_model_asset_record,
    compute_sha256,
    read_model_manifest,
)


def test_missing_detector_and_embedder_files_are_reported(tmp_path) -> None:
    settings = Settings(
        model_asset_dir=str(tmp_path),
        yunet_model_path=str(tmp_path / "face_detection_yunet.onnx"),
        sface_model_path=str(tmp_path / "face_recognition_sface.onnx"),
        model_manifest_path=str(tmp_path / "model_manifest.json"),
    )

    status = ModelAssetManager(settings).status()

    assert status["manifest_state"] == MANIFEST_MISSING
    assert status["detector"]["exists"] is False
    assert status["detector"]["checksum_status"] == CHECKSUM_FILE_MISSING
    assert status["embedder"]["exists"] is False
    assert status["embedder"]["checksum_status"] == CHECKSUM_FILE_MISSING


def test_compute_sha256_and_checksum_match_mismatch(tmp_path) -> None:
    asset_path = tmp_path / "asset.bin"
    asset_path.write_bytes(b"hello world")
    expected = hashlib.sha256(b"hello world").hexdigest()

    assert compute_sha256(asset_path) == expected

    matching = build_model_asset_record(
        name="opencv-yunet",
        configured_path=str(asset_path),
        model_asset_dir=str(tmp_path),
        manifest_entry={"sha256": expected, "source": "verified source"},
    )
    assert matching.checksum_status == CHECKSUM_MATCH
    assert matching.checksum == expected

    mismatching = build_model_asset_record(
        name="opencv-yunet",
        configured_path=str(asset_path),
        model_asset_dir=str(tmp_path),
        manifest_entry={"sha256": "0" * 64, "source": "verified source"},
    )
    assert mismatching.checksum_status == CHECKSUM_MISMATCH
    assert mismatching.checksum == expected


def test_file_exists_without_expected_checksum_is_marked(tmp_path) -> None:
    asset_path = tmp_path / "asset.bin"
    asset_path.write_bytes(b"hello world")

    record = build_model_asset_record(
        name="opencv-yunet",
        configured_path=str(asset_path),
        model_asset_dir=str(tmp_path),
    )

    assert record.checksum_status == CHECKSUM_MISSING_EXPECTED
    assert record.checksum is None


def test_missing_manifest_is_handled_gracefully(tmp_path) -> None:
    manifest, state = read_model_manifest(tmp_path / "missing-manifest.json")

    assert manifest is None
    assert state == MANIFEST_MISSING
