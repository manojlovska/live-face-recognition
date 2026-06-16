from __future__ import annotations

import json

from app.config import get_settings
from app.services.config_validation import (
    DEFAULT_LOCAL_API_KEY,
    build_startup_diagnostics,
    should_fail_startup,
)


def _load_settings(monkeypatch, **env):
    get_settings.cache_clear()
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    return get_settings()


def _runtime_status(
    *,
    detector_state: str = "missing",
    embedder_state: str = "missing",
    gallery_state: str = "missing",
    include_paths: bool = True,
) -> dict[str, object]:
    assets = {
        "manifest_path": "models/model_manifest.json",
        "detector": {
            "path": "models/face_detection_yunet.onnx",
            "exists": False,
            "checksum_status": "file_missing",
        },
        "embedder": {
            "path": "models/face_recognition_sface.onnx",
            "exists": False,
            "checksum_status": "file_missing",
        },
    }
    gallery_details = {
        "state": gallery_state,
        "loaded": gallery_state == "loaded",
        "item_count": 0,
        "embedding_dim": None,
        "manifest_path": "data/gallery/gallery_manifest.json",
        "embeddings_path": "data/gallery/gallery_embeddings.npy",
        "metadata_path": "data/gallery/gallery_metadata.jsonl",
    }
    if not include_paths:
        assets["manifest_path"] = "models/model_manifest.json"

    return {
        "models": {"detector": detector_state, "embedder": embedder_state},
        "gallery": gallery_state,
        "assets": assets,
        "gallery_details": gallery_details,
    }


def _get_check(report: dict[str, object], name: str) -> dict[str, object]:
    for check in report["checks"]:
        if check["name"] == name:
            return check
    raise AssertionError(f"missing check: {name}")


def test_missing_api_key_reports_error(monkeypatch) -> None:
    settings = _load_settings(monkeypatch, APP_ENV="development")

    report = build_startup_diagnostics(settings, _runtime_status())

    check = _get_check(report, "api_key_configured")
    assert check["status"] == "error"
    assert report["status"] == "error"
    assert should_fail_startup(report, settings) is False


def test_default_local_key_warns_in_development(monkeypatch) -> None:
    settings = _load_settings(
        monkeypatch,
        APP_ENV="development",
        FACE_API_KEY=DEFAULT_LOCAL_API_KEY,
    )

    report = build_startup_diagnostics(settings, _runtime_status())

    check = _get_check(report, "api_key_default")
    assert check["status"] == "warning"
    assert report["status"] == "warning"


def test_default_local_key_errors_in_production(monkeypatch) -> None:
    settings = _load_settings(
        monkeypatch,
        APP_ENV="production",
        FACE_API_KEY=DEFAULT_LOCAL_API_KEY,
    )

    report = build_startup_diagnostics(settings, _runtime_status())

    check = _get_check(report, "api_key_default")
    assert check["status"] == "error"
    assert report["status"] == "error"
    assert should_fail_startup(report, settings) is True


def test_debug_image_retention_warns_in_development_and_errors_in_production(monkeypatch) -> None:
    dev_settings = _load_settings(
        monkeypatch,
        APP_ENV="development",
        FACE_API_KEY="local-dev-key",
        DEBUG_IMAGE_RETENTION="true",
    )
    dev_report = build_startup_diagnostics(dev_settings, _runtime_status())
    assert _get_check(dev_report, "debug_image_retention")["status"] == "warning"

    prod_settings = _load_settings(
        monkeypatch,
        APP_ENV="production",
        FACE_API_KEY="local-dev-key",
        DEBUG_IMAGE_RETENTION="true",
    )
    prod_report = build_startup_diagnostics(prod_settings, _runtime_status())
    assert _get_check(prod_report, "debug_image_retention")["status"] == "error"
    assert should_fail_startup(prod_report, prod_settings) is True


def test_invalid_app_env_errors(monkeypatch) -> None:
    settings = _load_settings(monkeypatch, APP_ENV="banana", FACE_API_KEY="local-dev-key")

    report = build_startup_diagnostics(settings, _runtime_status())

    check = _get_check(report, "app_env_valid")
    assert check["status"] == "error"
    assert should_fail_startup(report, settings) is True


def test_invalid_max_image_bytes_errors(monkeypatch) -> None:
    settings = _load_settings(
        monkeypatch,
        APP_ENV="development",
        FACE_API_KEY="local-dev-key",
        FACE_MAX_IMAGE_BYTES="0",
    )

    report = build_startup_diagnostics(settings, _runtime_status())

    check = _get_check(report, "max_image_bytes")
    assert check["status"] == "error"


def test_startup_validate_assets_warns_in_development_and_errors_in_production(
    monkeypatch,
) -> None:
    dev_settings = _load_settings(
        monkeypatch,
        APP_ENV="development",
        FACE_API_KEY="local-dev-key",
        STARTUP_VALIDATE_ASSETS="false",
    )
    dev_report = build_startup_diagnostics(dev_settings, _runtime_status())
    assert _get_check(dev_report, "startup_validate_assets")["status"] == "warning"

    prod_settings = _load_settings(
        monkeypatch,
        APP_ENV="production",
        FACE_API_KEY="local-dev-key",
        STARTUP_VALIDATE_ASSETS="false",
    )
    prod_report = build_startup_diagnostics(prod_settings, _runtime_status())
    assert _get_check(prod_report, "startup_validate_assets")["status"] == "error"


def test_too_large_max_image_bytes_warns_in_development_and_errors_in_production(
    monkeypatch,
) -> None:
    dev_settings = _load_settings(
        monkeypatch,
        APP_ENV="development",
        FACE_API_KEY="local-dev-key",
        FACE_MAX_IMAGE_BYTES=str(11 * 1024 * 1024),
    )
    dev_report = build_startup_diagnostics(dev_settings, _runtime_status())
    assert _get_check(dev_report, "max_image_bytes")["status"] == "warning"

    prod_settings = _load_settings(
        monkeypatch,
        APP_ENV="production",
        FACE_API_KEY="local-dev-key",
        FACE_MAX_IMAGE_BYTES=str(11 * 1024 * 1024),
    )
    prod_report = build_startup_diagnostics(prod_settings, _runtime_status())
    assert _get_check(prod_report, "max_image_bytes")["status"] == "error"


def test_missing_model_assets_with_auto_load_true_reports_clear_check(monkeypatch) -> None:
    settings = _load_settings(
        monkeypatch,
        APP_ENV="development",
        FACE_API_KEY="local-dev-key",
        MODEL_AUTO_LOAD="true",
    )

    report = build_startup_diagnostics(settings, _runtime_status())

    check = _get_check(report, "model_assets_ready")
    assert check["status"] == "warning"
    assert "MODEL_AUTO_LOAD is enabled" in check["message"]


def test_missing_gallery_with_auto_load_true_reports_clear_check(monkeypatch) -> None:
    settings = _load_settings(
        monkeypatch,
        APP_ENV="development",
        FACE_API_KEY="local-dev-key",
        GALLERY_AUTO_LOAD="true",
    )

    report = build_startup_diagnostics(settings, _runtime_status())

    check = _get_check(report, "gallery_assets_ready")
    assert check["status"] == "warning"
    assert "GALLERY_AUTO_LOAD is enabled" in check["message"]


def test_diagnostics_do_not_include_raw_api_key_or_paths(monkeypatch) -> None:
    settings = _load_settings(
        monkeypatch,
        APP_ENV="development",
        FACE_API_KEY="local-dev-key",
    )

    report = build_startup_diagnostics(settings, _runtime_status())
    text = json.dumps(report)

    assert "local-dev-key" not in text
    assert "models/model_manifest.json" not in text
    assert "data/gallery/gallery_manifest.json" not in text
