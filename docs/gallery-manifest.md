# Gallery Manifest

## Purpose
The gallery manifest records how a gallery artifact was built. It protects reproducibility and prevents confusion between incompatible embeddings.
This is separate from the model asset manifest used to record YuNet/SFace model file checksums.

The current runtime supports a v1 local gallery artifact format for tests and small local deployments. It does not require a CelebA-specific SQLite database.
The sample builder writes this same runtime format.

## Manifest Fields

```json
{
  "gallery_version": "test-gallery-v1",
  "detector_model": "opencv-yunet",
  "embedding_model": "opencv-sface",
  "embedding_dim": 128,
  "distance": "cosine",
  "metadata_format": "jsonl",
  "item_count": 3,
  "identity_count": 2,
  "created_by": "test_fixture",
  "source": {
    "dataset": "CelebA-like local sample",
    "images_dir": "/abs/path/to/images",
    "identity_file": "/abs/path/to/identity.txt"
  },
  "notes": "Tiny gallery for tests; not CelebA."
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
    "embedding_failed": 1
  },
  "warnings": {
    "multiple_faces_used_best": 3
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

## Update Rule
Whenever gallery format changes, update this file and add or update tests.

## Model Manifest Distinction
- The model manifest documents detector/embedder asset provenance and checksums.
- The gallery manifest documents gallery artifact provenance and runtime search assumptions.
- The build report documents build-time outcomes and skip reasons.
- Do not mix model asset metadata into the gallery manifest.
