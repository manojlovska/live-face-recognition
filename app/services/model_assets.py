from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from app.config import Settings

CHECKSUM_NOT_CHECKED: Final = "not_checked"
CHECKSUM_MISSING_EXPECTED: Final = "missing_expected_checksum"
CHECKSUM_MATCH: Final = "match"
CHECKSUM_MISMATCH: Final = "mismatch"
CHECKSUM_FILE_MISSING: Final = "file_missing"

MANIFEST_MISSING: Final = "missing"
MANIFEST_LOADED: Final = "loaded"
MANIFEST_INVALID: Final = "invalid"


@dataclass(slots=True)
class ModelAssetRecord:
    name: str
    path: str
    exists: bool
    checksum_status: str
    checksum: str | None = None
    expected_sha256: str | None = None
    source: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "path": self.path,
            "exists": self.exists,
            "checksum_status": self.checksum_status,
            "checksum": self.checksum,
            "expected_sha256": self.expected_sha256,
            "source": self.source,
        }


def compute_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_model_path(configured_path: str, model_asset_dir: str) -> Path:
    path = Path(configured_path)
    if path.is_absolute():
        return path

    asset_dir = Path(model_asset_dir)
    if path.parts[: len(asset_dir.parts)] == asset_dir.parts:
        return path

    return asset_dir / path


def read_model_manifest(path: str | Path) -> tuple[dict[str, Any] | None, str]:
    manifest_path = Path(path)
    if not manifest_path.is_file():
        return None, MANIFEST_MISSING

    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, MANIFEST_INVALID

    if not isinstance(raw, dict):
        return None, MANIFEST_INVALID

    return raw, MANIFEST_LOADED


def _manifest_entry(manifest: dict[str, Any] | None, key: str) -> dict[str, Any] | None:
    if manifest is None:
        return None

    entry = manifest.get(key)
    return entry if isinstance(entry, dict) else None


def build_model_asset_record(
    *,
    name: str,
    configured_path: str,
    model_asset_dir: str,
    manifest_entry: dict[str, Any] | None = None,
) -> ModelAssetRecord:
    resolved_path = resolve_model_path(configured_path, model_asset_dir)
    exists = resolved_path.is_file()
    expected_sha256 = None
    source = None
    if manifest_entry is not None:
        expected_sha256 = _string_or_none(manifest_entry.get("sha256"))
        source = _string_or_none(manifest_entry.get("source"))

    if not exists:
        checksum_status = CHECKSUM_FILE_MISSING
        checksum = None
    elif expected_sha256 is None:
        checksum_status = CHECKSUM_MISSING_EXPECTED
        checksum = None
    else:
        checksum = compute_sha256(resolved_path)
        checksum_status = CHECKSUM_MATCH if checksum == expected_sha256 else CHECKSUM_MISMATCH

    return ModelAssetRecord(
        name=name,
        path=str(resolved_path),
        exists=exists,
        checksum_status=checksum_status,
        checksum=checksum,
        expected_sha256=expected_sha256,
        source=source,
    )


class ModelAssetManager:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @property
    def manifest_path(self) -> Path:
        return resolve_model_path(
            self._settings.model_manifest_path,
            self._settings.model_asset_dir,
        )

    def status(self) -> dict[str, object]:
        manifest, manifest_state = read_model_manifest(self.manifest_path)
        detector_entry = _manifest_entry(manifest, "detector")
        embedder_entry = _manifest_entry(manifest, "embedder")
        detector = build_model_asset_record(
            name="opencv-yunet",
            configured_path=self._settings.yunet_model_path,
            model_asset_dir=self._settings.model_asset_dir,
            manifest_entry=detector_entry,
        )
        embedder = build_model_asset_record(
            name="opencv-sface",
            configured_path=self._settings.sface_model_path,
            model_asset_dir=self._settings.model_asset_dir,
            manifest_entry=embedder_entry,
        )
        return {
            "manifest_path": str(self.manifest_path),
            "manifest_state": manifest_state,
            "detector": detector.as_dict(),
            "embedder": embedder.as_dict(),
        }


def _string_or_none(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None
