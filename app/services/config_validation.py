from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import Settings

ALLOWED_APP_ENVIRONMENTS = {"development", "test", "production"}
DEFAULT_LOCAL_API_KEY = "change-me-local-dev-key"
MAX_RECOMMENDED_IMAGE_BYTES = 10 * 1024 * 1024

_DEMO_HTML = Path(__file__).resolve().parents[1] / "static" / "demo.html"


@dataclass(slots=True)
class StartupCheck:
    name: str
    status: str
    severity: str
    message: str
    details: dict[str, Any] | None = None

    def to_public_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "status": self.status,
            "severity": self.severity,
            "message": self.message,
        }
        if self.details is not None:
            payload["details"] = self.details
        return payload


def build_startup_diagnostics(
    settings: Settings,
    runtime_status: dict[str, Any],
) -> dict[str, Any]:
    environment = _normalize_environment(settings.environment)
    include_paths = bool(settings.diagnostics_include_paths)
    checks: list[StartupCheck] = []

    _add_environment_check(checks, environment, settings.environment)
    _add_api_key_check(checks, settings, environment)
    _add_debug_retention_check(checks, settings, environment)
    _add_max_image_bytes_check(checks, settings, environment)
    _add_asset_validation_check(checks, settings, environment)
    _add_model_asset_check(checks, settings, runtime_status, environment, include_paths)
    _add_gallery_asset_check(checks, settings, runtime_status, environment, include_paths)
    _add_diagnostics_paths_check(checks, include_paths)
    _add_demo_availability_check(checks, include_paths)

    summary = {
        "errors": sum(1 for check in checks if check.status == "error"),
        "warnings": sum(1 for check in checks if check.status == "warning"),
    }
    status = "ok"
    if summary["errors"] > 0:
        status = "error"
    elif summary["warnings"] > 0:
        status = "warning"

    return {
        "object": "startup.diagnostics",
        "status": status,
        "environment": environment,
        "summary": summary,
        "checks": [check.to_public_dict() for check in checks],
    }


def should_fail_startup(report: dict[str, Any], settings: Settings) -> bool:
    if _has_error_check(report, "app_env_valid"):
        return True

    if settings.environment.strip().lower() == "production" and report["summary"]["errors"] > 0:
        return True

    if settings.strict_startup_validation and report["summary"]["errors"] > 0:
        return True

    return False


def format_startup_failure_message(report: dict[str, Any]) -> str:
    failing_checks = [
        f"{check['name']}: {check['message']}"
        for check in report["checks"]
        if check["status"] == "error"
    ]
    summary = report["summary"]
    return (
        "Startup validation failed "
        f"(environment={report['environment']}, errors={summary['errors']}, "
        f"warnings={summary['warnings']}). " + "; ".join(failing_checks)
    )


def _add_environment_check(
    checks: list[StartupCheck],
    environment: str,
    configured_environment: str,
) -> None:
    if environment not in ALLOWED_APP_ENVIRONMENTS:
        checks.append(
            StartupCheck(
                name="app_env_valid",
                status="error",
                severity="error",
                message=(
                    "APP_ENV must be one of development, test, or production. "
                    f"Got {configured_environment!r}."
                ),
            )
        )
        return

    checks.append(
        StartupCheck(
            name="app_env_valid",
            status="ok",
            severity="error",
            message=f"APP_ENV is set to {environment}.",
        )
    )


def _add_api_key_check(
    checks: list[StartupCheck],
    settings: Settings,
    environment: str,
) -> None:
    api_key = (settings.face_api_key or "").strip()
    if not api_key:
        checks.append(
            StartupCheck(
                name="api_key_configured",
                status="error",
                severity="error",
                message="FACE_API_KEY is not configured.",
            )
        )
        return

    if api_key == DEFAULT_LOCAL_API_KEY:
        status = "error" if environment == "production" else "warning"
        checks.append(
            StartupCheck(
                name="api_key_default",
                status=status,
                severity="error",
                message="FACE_API_KEY uses the default local development value.",
            )
        )
        return

    checks.append(
        StartupCheck(
            name="api_key_configured",
            status="ok",
            severity="error",
            message="FACE_API_KEY is configured.",
        )
    )


def _add_debug_retention_check(
    checks: list[StartupCheck],
    settings: Settings,
    environment: str,
) -> None:
    if settings.debug_image_retention:
        status = "error" if environment == "production" else "warning"
        checks.append(
            StartupCheck(
                name="debug_image_retention",
                status=status,
                severity="error",
                message="DEBUG_IMAGE_RETENTION is enabled.",
            )
        )
        return

    checks.append(
        StartupCheck(
            name="debug_image_retention",
            status="ok",
            severity="error",
            message="DEBUG_IMAGE_RETENTION is disabled.",
        )
    )


def _add_max_image_bytes_check(
    checks: list[StartupCheck],
    settings: Settings,
    environment: str,
) -> None:
    max_image_bytes = int(settings.max_image_bytes)
    if max_image_bytes <= 0:
        checks.append(
            StartupCheck(
                name="max_image_bytes",
                status="error",
                severity="error",
                message="FACE_MAX_IMAGE_BYTES must be greater than zero.",
            )
        )
        return

    if max_image_bytes > MAX_RECOMMENDED_IMAGE_BYTES:
        status = "error" if environment == "production" else "warning"
        checks.append(
            StartupCheck(
                name="max_image_bytes",
                status=status,
                severity="error",
                message=(
                    "FACE_MAX_IMAGE_BYTES exceeds the recommended startup limit "
                    f"of {MAX_RECOMMENDED_IMAGE_BYTES} bytes."
                ),
            )
        )
        return

    checks.append(
        StartupCheck(
            name="max_image_bytes",
            status="ok",
            severity="error",
            message=f"FACE_MAX_IMAGE_BYTES is set to {max_image_bytes} bytes.",
        )
    )


def _add_asset_validation_check(
    checks: list[StartupCheck],
    settings: Settings,
    environment: str,
) -> None:
    if settings.startup_validate_assets:
        checks.append(
            StartupCheck(
                name="startup_validate_assets",
                status="ok",
                severity="warning",
                message="Startup asset validation is enabled.",
            )
        )
        return

    status = "error" if environment == "production" else "warning"
    checks.append(
        StartupCheck(
            name="startup_validate_assets",
            status=status,
            severity="warning",
            message="STARTUP_VALIDATE_ASSETS is disabled.",
        )
    )


def _add_model_asset_check(
    checks: list[StartupCheck],
    settings: Settings,
    runtime_status: dict[str, Any],
    environment: str,
    include_paths: bool,
) -> None:
    models_status = runtime_status.get("models")
    if not settings.model_auto_load:
        checks.append(
            StartupCheck(
                name="model_assets_ready",
                status="ok",
                severity="error",
                message="MODEL_AUTO_LOAD is disabled.",
                details=_model_details(runtime_status, include_paths),
            )
        )
        return

    detector_state, embedder_state = _model_states(models_status)
    if detector_state == "loaded" and embedder_state == "loaded":
        checks.append(
            StartupCheck(
                name="model_assets_ready",
                status="ok",
                severity="error",
                message="Model assets are loaded.",
                details=_model_details(runtime_status, include_paths),
            )
        )
        return

    status = "error" if settings.strict_startup_validation else "warning"
    message = (
        "MODEL_AUTO_LOAD is enabled but the model assets are not fully loaded "
        f"(detector={detector_state}, embedder={embedder_state})."
    )
    checks.append(
        StartupCheck(
            name="model_assets_ready",
            status=status,
            severity="error",
            message=message,
            details=_model_details(runtime_status, include_paths),
        )
    )


def _add_gallery_asset_check(
    checks: list[StartupCheck],
    settings: Settings,
    runtime_status: dict[str, Any],
    environment: str,
    include_paths: bool,
) -> None:
    gallery_state = str(runtime_status.get("gallery", "missing"))
    if not settings.gallery_auto_load:
        checks.append(
            StartupCheck(
                name="gallery_assets_ready",
                status="ok",
                severity="error",
                message="GALLERY_AUTO_LOAD is disabled.",
                details=_gallery_details(runtime_status, include_paths),
            )
        )
        return

    if gallery_state == "loaded":
        checks.append(
            StartupCheck(
                name="gallery_assets_ready",
                status="ok",
                severity="error",
                message="Gallery artifacts are loaded.",
                details=_gallery_details(runtime_status, include_paths),
            )
        )
        return

    status = "error" if settings.strict_startup_validation else "warning"
    checks.append(
        StartupCheck(
            name="gallery_assets_ready",
            status=status,
            severity="error",
            message=(
                "GALLERY_AUTO_LOAD is enabled but the gallery artifacts are not fully loaded "
                f"(state={gallery_state})."
            ),
            details=_gallery_details(runtime_status, include_paths),
        )
    )


def _add_diagnostics_paths_check(
    checks: list[StartupCheck],
    include_paths: bool,
) -> None:
    if include_paths:
        checks.append(
            StartupCheck(
                name="diagnostics_include_paths",
                status="warning",
                severity="warning",
                message="Diagnostics will include selected path values.",
            )
        )
        return

    checks.append(
        StartupCheck(
            name="diagnostics_include_paths",
            status="ok",
            severity="warning",
            message="Diagnostics path values are redacted.",
        )
    )


def _add_demo_availability_check(
    checks: list[StartupCheck],
    include_paths: bool,
) -> None:
    if _DEMO_HTML.is_file():
        details = {"available": True}
        if include_paths:
            details["path"] = str(_DEMO_HTML)
        checks.append(
            StartupCheck(
                name="browser_demo_available",
                status="ok",
                severity="info",
                message="Browser demo assets are present.",
                details=details,
            )
        )
        return

    checks.append(
        StartupCheck(
            name="browser_demo_available",
            status="warning",
            severity="warning",
            message="Browser demo assets are missing.",
        )
    )


def _model_states(models_status: Any) -> tuple[str, str]:
    if not isinstance(models_status, dict):
        return "missing", "missing"

    detector_state = str(models_status.get("detector", "missing"))
    embedder_state = str(models_status.get("embedder", "missing"))
    return detector_state, embedder_state


def _model_details(runtime_status: dict[str, Any], include_paths: bool) -> dict[str, Any]:
    details: dict[str, Any] = {}
    assets = runtime_status.get("assets")
    gallery_details = runtime_status.get("gallery_details")
    models_status = runtime_status.get("models")

    if isinstance(models_status, dict):
        details["detector_state"] = models_status.get("detector")
        details["embedder_state"] = models_status.get("embedder")

    gallery_state = runtime_status.get("gallery")
    if isinstance(gallery_state, str):
        details["gallery_state"] = gallery_state

    if include_paths and isinstance(assets, dict):
        details["paths"] = {
            "model_manifest_path": assets.get("manifest_path"),
        }
        detector = assets.get("detector")
        embedder = assets.get("embedder")
        if isinstance(detector, dict):
            details["paths"]["detector_path"] = detector.get("path")
        if isinstance(embedder, dict):
            details["paths"]["embedder_path"] = embedder.get("path")
    if include_paths and isinstance(gallery_details, dict):
        details.setdefault("paths", {}).update(
            {
                "gallery_manifest_path": gallery_details.get("manifest_path"),
                "gallery_embeddings_path": gallery_details.get("embeddings_path"),
                "gallery_metadata_path": gallery_details.get("metadata_path"),
            }
        )

    return details


def _gallery_details(runtime_status: dict[str, Any], include_paths: bool) -> dict[str, Any]:
    details: dict[str, Any] = {}
    gallery_details = runtime_status.get("gallery_details")
    if isinstance(gallery_details, dict):
        details["gallery_state"] = gallery_details.get("state")
        details["gallery_loaded"] = gallery_details.get("loaded")
        details["item_count"] = gallery_details.get("item_count")
        details["embedding_dim"] = gallery_details.get("embedding_dim")
        if include_paths:
            details["paths"] = {
                "gallery_manifest_path": gallery_details.get("manifest_path"),
                "gallery_embeddings_path": gallery_details.get("embeddings_path"),
                "gallery_metadata_path": gallery_details.get("metadata_path"),
            }
    return details


def _normalize_environment(environment: str) -> str:
    return environment.strip().lower()


def _has_error_check(report: dict[str, Any], name: str) -> bool:
    for check in report.get("checks", []):
        if isinstance(check, dict) and check.get("name") == name and check.get("status") == "error":
            return True
    return False
