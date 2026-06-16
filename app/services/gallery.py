from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from app.config import Settings
from app.core.errors import GalleryStateError

GALLERY_STATE_MISSING = "missing"
GALLERY_STATE_PRESENT_NOT_LOADED = "present_not_loaded"
GALLERY_STATE_LOADED = "loaded"
GALLERY_STATE_ERROR = "error"


@dataclass(slots=True)
class GalleryMetadataRow:
    row: int
    celeba_identity_id: str
    display_name: str | None
    source_image: str | None
    split: str | None

    @classmethod
    def from_dict(cls, row_index: int, data: dict[str, Any]) -> GalleryMetadataRow:
        metadata_row = data.get("row")
        if not isinstance(metadata_row, int) or metadata_row != row_index:
            raise GalleryStoreError(
                message="Gallery metadata row does not match embedding row.",
                code="gallery_metadata_row_mismatch",
            )

        celeba_identity_id = _require_string(data.get("celeba_identity_id"), "celeba_identity_id")
        display_name = _string_or_none(data.get("display_name"))
        source_image = _string_or_none(data.get("source_image"))
        split = _string_or_none(data.get("split"))
        return cls(
            row=row_index,
            celeba_identity_id=celeba_identity_id,
            display_name=display_name,
            source_image=source_image,
            split=split,
        )

    def to_public_dict(self) -> dict[str, object]:
        return {
            "row": self.row,
            "celeba_identity_id": self.celeba_identity_id,
            "display_name": self.display_name,
            "source_image": self.source_image,
            "split": self.split,
        }


@dataclass(slots=True)
class GalleryMatch:
    rank: int
    celeba_identity_id: str
    display_name: str | None
    similarity: float
    source_image: str | None

    def to_public_dict(self) -> dict[str, object]:
        return {
            "rank": self.rank,
            "celeba_identity_id": self.celeba_identity_id,
            "display_name": self.display_name,
            "similarity": float(round(self.similarity, 6)),
            "source_image": self.source_image,
        }


class GalleryStoreError(GalleryStateError):
    pass


@dataclass(slots=True)
class GalleryArtifactBundle:
    embeddings: np.ndarray | None = None
    normalized_embeddings: np.ndarray | None = None
    metadata: list[GalleryMetadataRow] | None = None
    manifest: dict[str, Any] | None = None


class GalleryStore:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._state = GALLERY_STATE_MISSING
        self._load_attempted = False
        self._error: str | None = None
        self._error_code: str | None = None
        self._manifest_state = "missing"
        self._manifest: dict[str, Any] | None = None
        self._items = GalleryArtifactBundle()
        self._embedding_dim: int | None = None
        self._item_count = 0

    @property
    def manifest_path(self) -> Path:
        return resolve_gallery_path(
            self._settings.gallery_manifest_path,
            self._settings.gallery_dir,
        )

    @property
    def embeddings_path(self) -> Path:
        return resolve_gallery_path(
            self._settings.gallery_embeddings_path,
            self._settings.gallery_dir,
        )

    @property
    def metadata_path(self) -> Path:
        return resolve_gallery_path(
            self._settings.gallery_metadata_path,
            self._settings.gallery_dir,
        )

    @property
    def state(self) -> str:
        if self._state in {GALLERY_STATE_LOADED, GALLERY_STATE_ERROR}:
            return self._state
        if self._load_attempted:
            return self._state
        if self._artifacts_exist():
            return GALLERY_STATE_PRESENT_NOT_LOADED
        return GALLERY_STATE_MISSING

    @property
    def embedding_dim(self) -> int | None:
        return self._embedding_dim

    @property
    def item_count(self) -> int:
        return self._item_count

    @property
    def version(self) -> str | None:
        if self._manifest is None:
            return None
        value = self._manifest.get("gallery_version")
        return value if isinstance(value, str) else None

    def is_loaded(self) -> bool:
        return self.state == GALLERY_STATE_LOADED and self._items.normalized_embeddings is not None

    def load(self) -> dict[str, object]:
        self._load_attempted = True
        self._error = None
        self._error_code = None
        self._manifest = None
        self._items = GalleryArtifactBundle()
        self._embedding_dim = None
        self._item_count = 0

        try:
            manifest, manifest_state = read_gallery_manifest(self.manifest_path)
            self._manifest_state = manifest_state
            if manifest is None:
                self._state = GALLERY_STATE_MISSING
                self._error_code = "gallery_manifest_missing"
                return self.status()

            embeddings = self._load_embeddings(self.embeddings_path)
            metadata = self._load_metadata(self.metadata_path)
            self._validate_manifest(manifest, embeddings, metadata)
            normalized_embeddings = _normalize_rows(embeddings)

            self._manifest = manifest
            self._items = GalleryArtifactBundle(
                embeddings=embeddings,
                normalized_embeddings=normalized_embeddings,
                metadata=metadata,
                manifest=manifest,
            )
            self._embedding_dim = int(embeddings.shape[1])
            self._item_count = int(embeddings.shape[0])
            self._state = GALLERY_STATE_LOADED
            return self.status()
        except GalleryStoreError as exc:
            self._state = GALLERY_STATE_ERROR
            self._error = exc.message
            self._error_code = exc.code
            return self.status()
        except FileNotFoundError as exc:
            self._state = GALLERY_STATE_MISSING
            self._error = str(exc)
            self._error_code = "gallery_file_missing"
            return self.status()
        except OSError as exc:
            self._state = GALLERY_STATE_ERROR
            self._error = f"gallery_load_failed: {exc.__class__.__name__}: {exc}"
            self._error_code = "gallery_load_failed"
            return self.status()

    def status(self) -> dict[str, object]:
        return {
            "state": self.state,
            "loaded": self.is_loaded(),
            "load_attempted": self._load_attempted,
            "error": self._error,
            "error_code": self._error_code,
            "manifest_state": self._manifest_state,
            "manifest_path": str(self.manifest_path),
            "embeddings_path": str(self.embeddings_path),
            "metadata_path": str(self.metadata_path),
            "version": self.version,
            "item_count": self._item_count,
            "embedding_dim": self._embedding_dim,
        }

    def summary(self) -> dict[str, object]:
        return {
            "state": self.state,
            "version": self.version,
            "item_count": self._item_count,
            "embedding_dim": self._embedding_dim,
        }

    def search(self, query_embedding: np.ndarray, top_k: int) -> list[GalleryMatch]:
        if not self.is_loaded() or self._items.normalized_embeddings is None:
            raise GalleryStoreError(
                message="Gallery is not loaded.",
                code="gallery_not_loaded",
                status_code=503,
                error_type="service_unavailable",
            )

        query_vector = np.asarray(query_embedding, dtype=np.float32).reshape(-1)
        if query_vector.size != self._embedding_dim:
            raise GalleryStoreError(
                message="Query embedding dimension does not match gallery embedding dimension.",
                code="embedding_dimension_mismatch",
                status_code=500,
                error_type="invalid_gallery_state",
            )

        query_normalized = _normalize_vector(query_vector)
        similarities = self._items.normalized_embeddings @ query_normalized
        limit = min(int(top_k), int(similarities.shape[0]))
        if limit <= 0:
            return []

        ranked_indices = np.argsort(-similarities)[:limit]
        matches: list[GalleryMatch] = []
        for rank, index in enumerate(ranked_indices, start=1):
            metadata = self._items.metadata[index] if self._items.metadata is not None else None
            matches.append(
                GalleryMatch(
                    rank=rank,
                    celeba_identity_id=(
                        metadata.celeba_identity_id if metadata is not None else str(index)
                    ),
                    display_name=metadata.display_name if metadata is not None else None,
                    similarity=float(similarities[index]),
                    source_image=metadata.source_image if metadata is not None else None,
                )
            )
        return matches

    def _load_embeddings(self, path: Path) -> np.ndarray:
        if not path.is_file():
            raise FileNotFoundError(path)

        try:
            embeddings = np.load(path, allow_pickle=False)
        except ValueError as exc:
            raise GalleryStoreError(
                message="Gallery embeddings file is invalid.",
                code="gallery_embeddings_invalid",
            ) from exc
        array = np.asarray(embeddings, dtype=np.float32)
        if array.ndim != 2 or array.size == 0:
            raise GalleryStoreError(
                message="Gallery embeddings must be a 2D array.",
                code="gallery_embeddings_invalid",
            )
        return array

    def _load_metadata(self, path: Path) -> list[GalleryMetadataRow]:
        if not path.is_file():
            raise FileNotFoundError(path)

        metadata_rows: list[GalleryMetadataRow] = []
        with path.open("r", encoding="utf-8") as handle:
            for index, line in enumerate(handle):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise GalleryStoreError(
                        message="Gallery metadata JSONL is invalid.",
                        code="gallery_metadata_invalid",
                    ) from exc
                if not isinstance(data, dict):
                    raise GalleryStoreError(
                        message="Gallery metadata row must be a JSON object.",
                        code="gallery_metadata_invalid",
                    )
                metadata_rows.append(GalleryMetadataRow.from_dict(index, data))

        if not metadata_rows:
            raise GalleryStoreError(
                message="Gallery metadata is empty.",
                code="gallery_metadata_empty",
            )
        return metadata_rows

    def _validate_manifest(
        self,
        manifest: dict[str, Any],
        embeddings: np.ndarray,
        metadata: list[GalleryMetadataRow],
    ) -> None:
        required_fields = (
            "gallery_version",
            "embedding_model",
            "embedding_dim",
            "distance",
            "metadata_format",
            "item_count",
        )
        for field_name in required_fields:
            if field_name not in manifest:
                raise GalleryStoreError(
                    message=f"Gallery manifest is missing required field: {field_name}.",
                    code="gallery_manifest_invalid",
                )

        embedding_dim = manifest["embedding_dim"]
        item_count = manifest["item_count"]
        metadata_format = manifest["metadata_format"]
        distance = manifest["distance"]
        if not isinstance(embedding_dim, int) or embedding_dim <= 0:
            raise GalleryStoreError(
                message="Gallery manifest embedding dimension is invalid.",
                code="gallery_manifest_invalid",
            )
        if not isinstance(item_count, int) or item_count <= 0:
            raise GalleryStoreError(
                message="Gallery manifest item count is invalid.",
                code="gallery_manifest_invalid",
            )
        if metadata_format != "jsonl":
            raise GalleryStoreError(
                message="Gallery manifest metadata format must be jsonl.",
                code="gallery_manifest_invalid",
            )
        if distance != "cosine":
            raise GalleryStoreError(
                message="Gallery manifest distance must be cosine.",
                code="gallery_manifest_invalid",
            )
        if embeddings.shape[0] != item_count:
            raise GalleryStoreError(
                message="Gallery item count does not match embeddings.",
                code="gallery_item_count_mismatch",
            )
        if embeddings.shape[1] != embedding_dim:
            raise GalleryStoreError(
                message="Gallery embedding dimension does not match manifest.",
                code="gallery_embedding_dimension_mismatch",
            )
        if len(metadata) != item_count:
            raise GalleryStoreError(
                message="Gallery metadata count does not match embeddings.",
                code="gallery_metadata_count_mismatch",
            )

    def _artifacts_exist(self) -> bool:
        return (
            self.manifest_path.is_file()
            and self.embeddings_path.is_file()
            and self.metadata_path.is_file()
        )


def resolve_gallery_path(configured_path: str, gallery_dir: str) -> Path:
    path = Path(configured_path)
    if path.is_absolute():
        return path

    asset_dir = Path(gallery_dir)
    if path.parts[: len(asset_dir.parts)] == asset_dir.parts:
        return path

    return asset_dir / path


def read_gallery_manifest(path: str | Path) -> tuple[dict[str, Any] | None, str]:
    manifest_path = Path(path)
    if not manifest_path.is_file():
        return None, "missing"

    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, "invalid"

    if not isinstance(raw, dict):
        return None, "invalid"

    return raw, "loaded"


def _normalize_rows(embeddings: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    return embeddings / norms


def _normalize_vector(vector: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if norm == 0:
        return vector.astype(np.float32)
    return vector / norm


def _require_string(value: object, field_name: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise GalleryStoreError(
        message=f"Gallery metadata field {field_name} is required.",
        code="gallery_metadata_invalid",
    )


def _string_or_none(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None
