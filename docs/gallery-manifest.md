# Gallery Manifest

## Purpose
The gallery manifest records how a gallery artifact was built. It protects reproducibility and prevents confusion between incompatible embeddings.

## Required Fields

```json
{
  "gallery_version": "celeba-sface-v1",
  "created_at": "ISO-8601 timestamp",
  "dataset": {
    "name": "CelebA",
    "source": "local path or documented source",
    "image_count_attempted": 0,
    "image_count_succeeded": 0,
    "image_count_failed": 0,
    "identity_count": 0
  },
  "detector": {
    "name": "YuNet",
    "file": "models/...",
    "checksum": "..."
  },
  "embedder": {
    "name": "SFace",
    "file": "models/...",
    "checksum": "...",
    "embedding_dim": 0
  },
  "preprocessing": {
    "image_size": null,
    "alignment": "...",
    "normalization": "..."
  },
  "artifacts": {
    "embeddings": "data/gallery/gallery_embeddings.npy",
    "metadata": "data/gallery/gallery_metadata.sqlite",
    "failed_images": "data/gallery/failed_images.csv"
  },
  "notes": "Similarity result only; not identity verification."
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
