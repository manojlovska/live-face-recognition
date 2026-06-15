from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from app.api.errors import GalleryStateError
from app.config import Settings
from app.services.gallery import (
    GALLERY_STATE_ERROR,
    GALLERY_STATE_LOADED,
    GALLERY_STATE_MISSING,
    GALLERY_STATE_PRESENT_NOT_LOADED,
    GalleryStore,
)

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "gallery"


def _build_settings(base_dir: Path) -> Settings:
    return Settings(
        gallery_dir=str(base_dir),
        gallery_embeddings_path=str(base_dir / "gallery_embeddings.npy"),
        gallery_metadata_path=str(base_dir / "gallery_metadata.jsonl"),
        gallery_manifest_path=str(base_dir / "gallery_manifest.json"),
    )


def test_gallery_store_reports_present_not_loaded_before_load() -> None:
    store = GalleryStore(_build_settings(FIXTURE_DIR))

    assert store.state == GALLERY_STATE_PRESENT_NOT_LOADED
    assert store.is_loaded() is False


def test_gallery_store_loads_valid_gallery() -> None:
    store = GalleryStore(_build_settings(FIXTURE_DIR))

    status = store.load()

    assert status["state"] == GALLERY_STATE_LOADED
    assert status["loaded"] is True
    assert status["version"] == "test-gallery-v1"
    assert status["item_count"] == 3
    assert status["embedding_dim"] == 128


def test_gallery_store_rejects_missing_embeddings_file(tmp_path) -> None:
    gallery_dir = tmp_path / "gallery"
    gallery_dir.mkdir()
    (gallery_dir / "gallery_metadata.jsonl").write_text(
        json.dumps(
            {
                "row": 0,
                "celeba_identity_id": "test_identity_001",
                "display_name": None,
                "source_image": None,
                "split": "test_fixture",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (gallery_dir / "gallery_manifest.json").write_text(
        json.dumps(
            {
                "gallery_version": "test-gallery-v1",
                "embedding_model": "opencv-sface",
                "embedding_dim": 128,
                "distance": "cosine",
                "metadata_format": "jsonl",
                "item_count": 1,
                "created_by": "test_fixture",
            }
        ),
        encoding="utf-8",
    )

    store = GalleryStore(_build_settings(gallery_dir))
    status = store.load()

    assert status["state"] == GALLERY_STATE_MISSING
    assert status["error_code"] == "gallery_file_missing"


def test_gallery_store_rejects_metadata_count_mismatch(tmp_path) -> None:
    gallery_dir = tmp_path / "gallery"
    gallery_dir.mkdir()
    embeddings = np.arange(3 * 128, dtype=np.float32).reshape(3, 128)
    np.save(gallery_dir / "gallery_embeddings.npy", embeddings)
    (gallery_dir / "gallery_metadata.jsonl").write_text(
        json.dumps(
            {
                "row": 0,
                "celeba_identity_id": "test_identity_001",
                "display_name": None,
                "source_image": None,
                "split": "test_fixture",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (gallery_dir / "gallery_manifest.json").write_text(
        json.dumps(
            {
                "gallery_version": "test-gallery-v1",
                "embedding_model": "opencv-sface",
                "embedding_dim": 128,
                "distance": "cosine",
                "metadata_format": "jsonl",
                "item_count": 3,
                "created_by": "test_fixture",
            }
        ),
        encoding="utf-8",
    )

    store = GalleryStore(_build_settings(gallery_dir))
    status = store.load()

    assert status["state"] == GALLERY_STATE_ERROR
    assert status["error_code"] == "gallery_metadata_count_mismatch"


def test_gallery_store_rejects_manifest_dimension_mismatch(tmp_path) -> None:
    gallery_dir = tmp_path / "gallery"
    gallery_dir.mkdir()
    embeddings = np.arange(3 * 128, dtype=np.float32).reshape(3, 128)
    np.save(gallery_dir / "gallery_embeddings.npy", embeddings)
    with (gallery_dir / "gallery_metadata.jsonl").open("w", encoding="utf-8") as handle:
        for row in range(3):
            handle.write(
                json.dumps(
                    {
                        "row": row,
                        "celeba_identity_id": f"test_identity_00{row + 1}",
                        "display_name": None,
                        "source_image": None,
                        "split": "test_fixture",
                    }
                )
                + "\n"
            )
    (gallery_dir / "gallery_manifest.json").write_text(
        json.dumps(
            {
                "gallery_version": "test-gallery-v1",
                "embedding_model": "opencv-sface",
                "embedding_dim": 4,
                "distance": "cosine",
                "metadata_format": "jsonl",
                "item_count": 3,
                "created_by": "test_fixture",
            }
        ),
        encoding="utf-8",
    )

    store = GalleryStore(_build_settings(gallery_dir))
    status = store.load()

    assert status["state"] == GALLERY_STATE_ERROR
    assert status["error_code"] == "gallery_embedding_dimension_mismatch"


def test_gallery_store_search_returns_sorted_top_k() -> None:
    store = GalleryStore(_build_settings(FIXTURE_DIR))
    store.load()
    query = np.arange(1, 129, dtype=np.float32)

    matches = store.search(query, top_k=2)

    assert [match.celeba_identity_id for match in matches] == [
        "test_identity_001",
        "test_identity_002",
    ]
    assert [match.rank for match in matches] == [1, 2]
    assert matches[0].similarity >= matches[1].similarity
    assert len(matches) == 2


def test_gallery_store_search_returns_fewer_than_top_k_when_gallery_is_smaller() -> None:
    store = GalleryStore(_build_settings(FIXTURE_DIR))
    store.load()
    query = np.arange(1, 129, dtype=np.float32)

    matches = store.search(query, top_k=10)

    assert len(matches) == 3


def test_gallery_store_search_detects_embedding_dimension_mismatch() -> None:
    store = GalleryStore(_build_settings(FIXTURE_DIR))
    store.load()

    with pytest.raises(GalleryStateError) as excinfo:
        store.search(np.ones(127, dtype=np.float32), top_k=5)

    assert excinfo.value.code == "embedding_dimension_mismatch"
