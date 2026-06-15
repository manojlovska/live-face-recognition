# Gallery Manifest

## Purpose
The gallery manifest records how a gallery artifact was built. It protects reproducibility and prevents confusion between incompatible embeddings.
This is separate from the model asset manifest used to record YuNet/SFace model file checksums.

The current runtime supports a v1 local gallery artifact format for tests and small local deployments. It does not require a CelebA-specific SQLite database.
The sample builder and CelebA-root builder both write this same runtime format.

## Manifest Fields

```json
{
  "gallery_version": "celeba-local-v1",
  "gallery_scope": "partial",
  "embedding_model": "opencv-sface",
  "detector_model": "opencv-yunet",
  "embedding_dim": 128,
  "distance": "cosine",
  "metadata_format": "jsonl",
  "item_count": 42,
  "identity_count": 20,
  "created_by": "scripts/build_gallery.py",
  "dataset": {
    "name": "CelebA",
    "source": "local_user_supplied",
    "root": "/abs/path/to/celeba",
    "identity_file": "/abs/path/to/identity_CelebA.txt",
    "partition_file": "/abs/path/to/list_eval_partition.txt"
  },
  "source": {
    "dataset": "CelebA",
    "images_dir": "/abs/path/to/img_align_celeba",
    "identity_file": "/abs/path/to/identity_CelebA.txt"
  },
  "filters": {
    "limit": 1000,
    "include_partitions": ["train", "val", "test"],
    "start_after": "000100.jpg",
    "min_detection_score": 0.85
  },
  "notes": "Sample gallery; not full CelebA."
}
```

## Build Report Fields

```json
{
  "attempted": 50,
  "succeeded": 42,
  "skipped": 8,
  "skip_reasons": {
    "no_face": 5,
    "decode_error": 2,
    "low_detection_score": 3,
    "embedding_failed": 1
  },
  "warnings": {
    "multiple_faces_used_best": 3
  },
  "quality": {
    "success_rate": 0.84,
    "identity_count": 20,
    "min_detection_score": 0.91,
    "mean_detection_score": 0.96,
    "median_detection_score": 0.97
  },
  "performance": {
    "started_at": "2026-06-15T10:00:00+00:00",
    "finished_at": "2026-06-15T10:00:10+00:00",
    "duration_seconds": 10.0,
    "images_per_second": 5.0,
    "mean_image_seconds": 0.2
  }
}
```

## Runtime Validation
At startup, the service should validate that:
- manifest exists;
- required artifact files exist;
- embedding dimension matches expected model output;
- gallery version is logged safely;
- missing/corrupt gallery causes `/readyz` to report not ready.

## Sample vs Full Gallery
- Sample gallery artifacts are for tests and small local runs.
- Local CelebA-root artifacts are user-supplied and may be partial or full.
- The manifest should record the actual scope and input filters.
- Full CelebA-scale processing remains a later work order.

## Update Rule
Whenever gallery format changes, update this file and add or update tests.

## Model Manifest Distinction
- The model manifest documents detector/embedder asset provenance and checksums.
- The gallery manifest documents gallery artifact provenance and runtime search assumptions.
- The build report documents build-time outcomes and skip reasons.
- Do not mix model asset metadata into the gallery manifest.
