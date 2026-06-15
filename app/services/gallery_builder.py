from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from PIL import Image, UnidentifiedImageError

from app.config import Settings, get_settings
from app.services.celeba_annotations import (
    CelebaAnnotationError,
    CelebAIdentityAnnotation,
    load_celeba_identity_annotations,
    load_celeba_partition_annotations,
)
from app.services.celeba_layout import CelebaLayout, CelebaLayoutError, discover_celeba_layout
from app.services.face_similarity import (
    DetectedFace,
    _generate_embedding,
    _run_yunet_detection,
)
from app.services.image_input import DecodedImage
from app.services.model_runtime import MODEL_STATE_LOADED, ModelRuntime

DEFAULT_CREATED_BY = "scripts/build_gallery.py"
DEFAULT_DATASET_NAME = "CelebA-like local sample"


class GalleryBuildError(Exception):
    def __init__(self, message: str, code: str) -> None:
        super().__init__(message)
        self.message = message
        self.code = code


@dataclass(slots=True)
class GalleryBuildReport:
    attempted: int = 0
    succeeded: int = 0
    skipped: int = 0
    skip_reasons: dict[str, int] = field(default_factory=dict)
    warnings: dict[str, int] = field(default_factory=dict)
    detection_scores: list[float] = field(default_factory=list, repr=False)
    quality: dict[str, object] = field(default_factory=dict)
    performance: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "attempted": self.attempted,
            "succeeded": self.succeeded,
            "skipped": self.skipped,
            "skip_reasons": dict(self.skip_reasons),
            "warnings": dict(self.warnings),
            "quality": dict(self.quality),
            "performance": dict(self.performance),
        }


@dataclass(slots=True)
class GalleryBuildResult:
    output_dir: Path
    embeddings_path: Path
    metadata_path: Path
    manifest_path: Path
    report_path: Path
    manifest: dict[str, object]
    report: GalleryBuildReport
    item_count: int
    embedding_dim: int | None
    identity_count: int

    def summary(self) -> dict[str, object]:
        return {
            "output_dir": str(self.output_dir),
            "embeddings_path": str(self.embeddings_path),
            "metadata_path": str(self.metadata_path),
            "manifest_path": str(self.manifest_path),
            "report_path": str(self.report_path),
            "item_count": self.item_count,
            "embedding_dim": self.embedding_dim,
            "identity_count": self.identity_count,
            "manifest": self.manifest,
            "report": self.report.to_dict(),
        }


class GalleryBuilder:
    def __init__(
        self,
        runtime: object | None = None,
        *,
        created_by: str = DEFAULT_CREATED_BY,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._runtime = runtime or ModelRuntime(self._settings)
        self._created_by = created_by

    def build(
        self,
        *,
        images_dir: str | Path | None = None,
        identity_file: str | Path | None = None,
        celeba_root: str | Path | None = None,
        partition_file: str | Path | None = None,
        include_partitions: list[str] | None = None,
        start_after: str | None = None,
        output_dir: str | Path,
        gallery_version: str,
        limit: int | None = None,
        overwrite: bool = False,
        dry_run: bool = False,
        fail_on_empty: bool = False,
        min_det_score: float = 0.0,
    ) -> GalleryBuildResult:
        output_path = Path(output_dir)

        if limit is not None and limit <= 0:
            raise GalleryBuildError(
                message="Limit must be positive when provided.",
                code="invalid_limit",
            )
        if min_det_score < 0:
            raise GalleryBuildError(
                message="Minimum detection score must be non-negative.",
                code="invalid_min_det_score",
            )

        resolved_layout = self._resolve_inputs(
            celeba_root=celeba_root,
            images_dir=images_dir,
            identity_file=identity_file,
            partition_file=partition_file,
        )
        images_path = resolved_layout.images_dir
        identity_path = resolved_layout.identity_file
        partition_path = resolved_layout.partition_file
        if include_partitions is not None and partition_path is None:
            raise GalleryBuildError(
                message="Partition filtering requires a partition file.",
                code="partition_filter_requires_partition_file",
            )

        normalized_partitions = self._normalize_partitions(include_partitions)
        try:
            annotations = load_celeba_identity_annotations(identity_path)
            partition_map = self._load_partition_map(partition_path)
        except CelebaAnnotationError as exc:
            raise GalleryBuildError(message=exc.message, code=exc.code) from exc
        annotations_to_process = self._select_annotations(
            annotations=annotations,
            partition_map=partition_map,
            default_split="sample" if resolved_layout.layout_kind == "explicit" else "unknown",
            include_partitions=normalized_partitions,
            start_after=start_after,
            sort_by_filename=resolved_layout.layout_kind != "explicit" or start_after is not None,
        )
        if limit is not None:
            annotations_to_process = annotations_to_process[:limit]

        detector, embedder = self._prepare_runtime()
        report = GalleryBuildReport()
        embeddings: list[np.ndarray] = []
        metadata_rows: list[dict[str, object]] = []
        identity_ids: set[str] = set()
        started_at = datetime.now(UTC)

        for annotation, split in annotations_to_process:
            report.attempted += 1
            image_path = images_path / annotation.image_filename
            if not image_path.is_file():
                self._record_skip(report, "missing_image")
                continue

            try:
                decoded_image = self._load_local_image(image_path)
            except GalleryBuildError:
                self._record_skip(report, "decode_error")
                continue

            bgr_image = decoded_image.rgb_array[:, :, ::-1].copy()
            detected_faces = _run_yunet_detection(
                detector,
                bgr_image,
                decoded_image.width,
                decoded_image.height,
            )
            if not detected_faces:
                self._record_skip(report, "no_face")
                continue

            chosen_face, warnings, low_score = self._choose_face(detected_faces, min_det_score)
            if chosen_face is None:
                self._record_skip(report, "low_detection_score" if low_score else "no_face")
                continue

            if warnings:
                for warning in warnings:
                    report.warnings[warning] = report.warnings.get(warning, 0) + 1

            embedding = _generate_embedding(embedder, chosen_face, bgr_image)
            if not embedding.generated or embedding.vector is None:
                self._record_skip(report, "embedding_failed")
                continue

            row_index = len(embeddings)
            embeddings.append(np.asarray(embedding.vector, dtype=np.float32).reshape(-1))
            identity_ids.add(annotation.identity_id)
            report.detection_scores.append(float(chosen_face.detection_score))
            metadata_rows.append(
                {
                    "row": row_index,
                    "celeba_identity_id": annotation.identity_id,
                    "display_name": None,
                    "source_image": annotation.image_filename,
                    "split": split,
                    "detection_score": float(round(chosen_face.detection_score, 6)),
                    "face_box": [int(round(value)) for value in chosen_face.box],
                    "warnings": warnings,
                }
            )
            report.succeeded += 1

        report.skipped = report.attempted - report.succeeded
        finished_at = datetime.now(UTC)
        self._finalize_report(
            report,
            started_at=started_at,
            finished_at=finished_at,
            identity_count=len(identity_ids),
        )

        if not dry_run and (report.succeeded == 0 or (fail_on_empty and report.attempted == 0)):
            raise GalleryBuildError(
                message="Gallery builder produced no usable embeddings.",
                code="gallery_empty",
            )

        manifest = self._build_manifest(
            gallery_version=gallery_version,
            embeddings=embeddings,
            identity_count=len(identity_ids),
            layout=resolved_layout,
            limit=limit,
            include_partitions=normalized_partitions,
            start_after=start_after,
            min_det_score=min_det_score,
        )
        result = GalleryBuildResult(
            output_dir=output_path,
            embeddings_path=output_path / "gallery_embeddings.npy",
            metadata_path=output_path / "gallery_metadata.jsonl",
            manifest_path=output_path / "gallery_manifest.json",
            report_path=output_path / "gallery_build_report.json",
            manifest=manifest,
            report=report,
            item_count=report.succeeded,
            embedding_dim=(
                manifest["embedding_dim"] if isinstance(manifest["embedding_dim"], int) else None
            ),
            identity_count=len(identity_ids),
        )

        if dry_run:
            return result

        self._ensure_output_dir(result.output_dir, overwrite=overwrite)
        self._write_outputs(
            result=result,
            embeddings=embeddings,
            metadata_rows=metadata_rows,
        )
        return result

    def _resolve_inputs(
        self,
        *,
        celeba_root: str | Path | None,
        images_dir: str | Path | None,
        identity_file: str | Path | None,
        partition_file: str | Path | None,
    ) -> CelebaLayout:
        if celeba_root is not None:
            try:
                layout = discover_celeba_layout(
                    celeba_root,
                    images_dir=images_dir,
                    identity_file=identity_file,
                    partition_file=partition_file,
                )
            except CelebaLayoutError as exc:
                raise GalleryBuildError(message=exc.message, code=exc.code) from exc
            return CelebaLayout(
                celeba_root=layout.celeba_root,
                images_dir=layout.images_dir,
                identity_file=layout.identity_file,
                partition_file=layout.partition_file,
                layout_kind=layout.layout_kind,
            )

        if images_dir is None or identity_file is None:
            raise GalleryBuildError(
                message=(
                    "Explicit images_dir and identity_file are required "
                    "when celeba_root is not provided."
                ),
                code="input_mode_invalid",
            )

        images_path = Path(images_dir)
        identity_path = Path(identity_file)
        if not images_path.is_dir():
            raise GalleryBuildError(
                message="Images directory does not exist.",
                code="images_dir_missing",
            )
        if not identity_path.is_file():
            raise GalleryBuildError(
                message="Identity annotation file does not exist.",
                code="identity_file_missing",
            )
        partition_path = Path(partition_file) if partition_file is not None else None
        if partition_path is not None and not partition_path.is_file():
            raise GalleryBuildError(
                message="Partition annotation file does not exist.",
                code="partition_file_missing",
            )
        return CelebaLayout(
            celeba_root=images_path.parent,
            images_dir=images_path,
            identity_file=identity_path,
            partition_file=partition_path,
            layout_kind="explicit",
        )

    def _select_annotations(
        self,
        *,
        annotations: list[CelebAIdentityAnnotation],
        partition_map: dict[str, str],
        default_split: str,
        include_partitions: list[str] | None,
        start_after: str | None,
        sort_by_filename: bool,
    ) -> list[tuple[CelebAIdentityAnnotation, str]]:
        selected_annotations = list(annotations)
        if sort_by_filename:
            selected_annotations = sorted(
                selected_annotations, key=lambda item: item.image_filename
            )

        allowed_partitions = set(include_partitions) if include_partitions is not None else None
        selected: list[tuple[CelebAIdentityAnnotation, str]] = []
        for annotation in selected_annotations:
            if start_after is not None and annotation.image_filename <= start_after:
                continue

            split = partition_map.get(annotation.image_filename, default_split)
            if allowed_partitions is not None and split not in allowed_partitions:
                continue

            selected.append((annotation, split))
        return selected

    @staticmethod
    def _normalize_partitions(include_partitions: list[str] | None) -> list[str] | None:
        if include_partitions is None:
            return None
        normalized = []
        for partition in include_partitions:
            value = partition.strip().lower()
            if value not in {"train", "val", "test"}:
                raise GalleryBuildError(
                    message="include_partitions must contain train, val, or test.",
                    code="invalid_include_partitions",
                )
            if value not in normalized:
                normalized.append(value)
        return normalized

    @staticmethod
    def _load_partition_map(partition_path: Path | None) -> dict[str, str]:
        if partition_path is None:
            return {}
        partition_annotations = load_celeba_partition_annotations(partition_path)
        return {
            annotation.image_filename: annotation.partition for annotation in partition_annotations
        }

    def _prepare_runtime(self) -> tuple[object, object]:
        load_models = getattr(self._runtime, "load_models", None)
        if callable(load_models):
            load_models()

        detector = getattr(self._runtime, "get_detector", lambda: None)()
        embedder = getattr(self._runtime, "get_embedder", lambda: None)()
        detector_state = getattr(self._runtime, "detector_state", lambda: None)()
        embedder_state = getattr(self._runtime, "embedder_state", lambda: None)()

        if detector is None or embedder is None:
            raise GalleryBuildError(
                message="YuNet and SFace models must be loaded before building a gallery.",
                code="model_runtime_not_ready",
            )
        if detector_state is not None and detector_state != MODEL_STATE_LOADED:
            raise GalleryBuildError(
                message="YuNet model is not loaded.",
                code="detector_not_loaded",
            )
        if embedder_state is not None and embedder_state != MODEL_STATE_LOADED:
            raise GalleryBuildError(
                message="SFace model is not loaded.",
                code="embedder_not_loaded",
            )
        return detector, embedder

    def _build_manifest(
        self,
        *,
        gallery_version: str,
        embeddings: list[np.ndarray],
        identity_count: int,
        layout: CelebaLayout,
        limit: int | None,
        include_partitions: list[str] | None,
        start_after: str | None,
        min_det_score: float,
    ) -> dict[str, object]:
        embedding_dim = embeddings[0].size if embeddings else 0
        gallery_scope = self._summarize_gallery_scope(
            layout=layout,
            limit=limit,
            include_partitions=include_partitions,
            start_after=start_after,
        )
        return {
            "gallery_version": gallery_version,
            "gallery_scope": gallery_scope,
            "embedding_model": "opencv-sface",
            "detector_model": "opencv-yunet",
            "embedding_dim": int(embedding_dim),
            "distance": "cosine",
            "metadata_format": "jsonl",
            "item_count": len(embeddings),
            "identity_count": identity_count,
            "created_by": self._created_by,
            "dataset": {
                "name": "CelebA" if layout.layout_kind != "explicit" else DEFAULT_DATASET_NAME,
                "source": "local_user_supplied",
                "root": str(layout.celeba_root.resolve()) if layout.celeba_root else None,
                "identity_file": str(layout.identity_file.resolve()),
                "partition_file": (
                    str(layout.partition_file.resolve()) if layout.partition_file else None
                ),
            },
            "source": {
                "dataset": DEFAULT_DATASET_NAME if layout.layout_kind == "explicit" else "CelebA",
                "images_dir": str(layout.images_dir.resolve()),
                "identity_file": str(layout.identity_file.resolve()),
            },
            "filters": {
                "limit": limit,
                "include_partitions": include_partitions,
                "start_after": start_after,
                "min_detection_score": min_det_score,
            },
            "notes": "Sample gallery; not full CelebA.",
        }

    @staticmethod
    def _summarize_gallery_scope(
        *,
        layout: CelebaLayout,
        limit: int | None,
        include_partitions: list[str] | None,
        start_after: str | None,
    ) -> str:
        if layout.layout_kind == "explicit":
            return "sample"
        if limit is not None or start_after is not None or include_partitions is not None:
            return "partial"
        return "full"

    def _ensure_output_dir(self, output_dir: Path, *, overwrite: bool) -> None:
        if output_dir.exists():
            existing_targets = [
                output_dir / "gallery_embeddings.npy",
                output_dir / "gallery_metadata.jsonl",
                output_dir / "gallery_manifest.json",
                output_dir / "gallery_build_report.json",
            ]
            if not overwrite and any(path.exists() for path in existing_targets):
                raise GalleryBuildError(
                    message="Output directory already contains gallery artifacts.",
                    code="output_exists",
                )
        else:
            output_dir.mkdir(parents=True, exist_ok=True)

    def _write_outputs(
        self,
        *,
        result: GalleryBuildResult,
        embeddings: list[np.ndarray],
        metadata_rows: list[dict[str, object]],
    ) -> None:
        result.output_dir.mkdir(parents=True, exist_ok=True)
        np.save(result.embeddings_path, np.stack(embeddings).astype(np.float32))
        with result.metadata_path.open("w", encoding="utf-8") as handle:
            for row in metadata_rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        result.manifest_path.write_text(
            json.dumps(result.manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        result.report_path.write_text(
            json.dumps(result.report.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def _choose_face(
        self,
        detected_faces: list[DetectedFace],
        min_det_score: float,
    ) -> tuple[DetectedFace | None, list[str], bool]:
        if not detected_faces:
            return None, [], False

        chosen_face = max(detected_faces, key=lambda face: face.detection_score)
        warnings: list[str] = []
        if len(detected_faces) > 1:
            warnings.append("multiple_faces_used_best")
        if chosen_face.detection_score < min_det_score:
            return None, warnings, True
        return chosen_face, warnings, False

    @staticmethod
    def _load_local_image(path: Path) -> DecodedImage:
        try:
            with Image.open(path) as image:
                original_format = image.format
                image.load()
                rgb_image = image.convert("RGB")
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise GalleryBuildError(
                message=f"Could not decode image: {path.name}",
                code="decode_error",
            ) from exc

        rgb_array = np.array(rgb_image, dtype=np.uint8)
        width, height = rgb_image.size
        mime_type = (
            f"image/{original_format.lower()}"
            if isinstance(original_format, str)
            else "image/unknown"
        )
        return DecodedImage(
            mime_type=mime_type,
            width=width,
            height=height,
            rgb_array=rgb_array,
        )

    @staticmethod
    def _record_skip(report: GalleryBuildReport, reason: str) -> None:
        report.skip_reasons[reason] = report.skip_reasons.get(reason, 0) + 1

    @staticmethod
    def _finalize_report(
        report: GalleryBuildReport,
        *,
        started_at: datetime,
        finished_at: datetime,
        identity_count: int,
    ) -> None:
        duration_seconds = max((finished_at - started_at).total_seconds(), 0.0)
        if report.attempted > 0:
            success_rate: float | None = report.succeeded / report.attempted
            images_per_second: float | None = (
                report.attempted / duration_seconds if duration_seconds > 0 else None
            )
            mean_image_seconds: float | None = duration_seconds / report.attempted
        else:
            success_rate = None
            images_per_second = None
            mean_image_seconds = None

        if report.detection_scores:
            score_array = np.asarray(report.detection_scores, dtype=np.float32)
            min_detection_score: float | None = float(np.min(score_array))
            mean_detection_score: float | None = float(np.mean(score_array))
            median_detection_score: float | None = float(np.median(score_array))
        else:
            min_detection_score = None
            mean_detection_score = None
            median_detection_score = None

        report.quality = {
            "success_rate": success_rate,
            "identity_count": identity_count,
            "min_detection_score": min_detection_score,
            "mean_detection_score": mean_detection_score,
            "median_detection_score": median_detection_score,
        }
        report.performance = {
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "duration_seconds": duration_seconds,
            "images_per_second": images_per_second,
            "mean_image_seconds": mean_image_seconds,
        }


def build_gallery(
    *,
    images_dir: str | Path | None = None,
    identity_file: str | Path | None = None,
    celeba_root: str | Path | None = None,
    partition_file: str | Path | None = None,
    include_partitions: list[str] | None = None,
    start_after: str | None = None,
    output_dir: str | Path,
    gallery_version: str,
    runtime: object | None = None,
    limit: int | None = None,
    overwrite: bool = False,
    dry_run: bool = False,
    fail_on_empty: bool = False,
    min_det_score: float = 0.0,
) -> GalleryBuildResult:
    builder = GalleryBuilder(runtime=runtime)
    result = builder.build(
        images_dir=images_dir,
        identity_file=identity_file,
        celeba_root=celeba_root,
        partition_file=partition_file,
        include_partitions=include_partitions,
        start_after=start_after,
        output_dir=output_dir,
        gallery_version=gallery_version,
        limit=limit,
        overwrite=overwrite,
        dry_run=dry_run,
        fail_on_empty=fail_on_empty,
        min_det_score=min_det_score,
    )
    return result
