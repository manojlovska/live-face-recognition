# Gallery Manifest

## Purpose
The gallery manifest records how a gallery artifact was built. It protects reproducibility and prevents confusion between incompatible embeddings.
This is separate from the model asset manifest used to record YuNet/SFace model file checksums.

The current runtime supports a v1 local gallery artifact format for tests and small local deployments. It does not require a CelebA-specific SQLite database.

## Required Fields

```json
{
  "gallery_version": "test-gallery-v1",
  "embedding_model": "opencv-sface",
  "embedding_dim": 128,
  "distance": "cosine",
  "metadata_format": "jsonl",
  "item_count": 3,
  "created_by": "test_fixture",
  "notes": "Tiny gallery for tests; not CelebA."
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
- Do not mix model asset metadata into the gallery manifest.
