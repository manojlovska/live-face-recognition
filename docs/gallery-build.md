# Gallery Build

## Purpose
The live API must not scan CelebA images at request time. Instead, an offline build process creates gallery artifacts used by the runtime service.
The runtime gallery loader is implemented now. The full CelebA build workflow remains future work.
The Work Order 9 builder skeleton processes a small CelebA-like sample directory and writes runtime-compatible gallery artifacts.

## Required Inputs
- Local image directory
- CelebA-style identity annotation file with `image_filename identity_id` rows
- YuNet model file
- SFace model file

## Sample Command

```bash
python scripts/build_gallery.py \
  --images-dir /path/to/sample/images \
  --identity-file /path/to/identity_sample.txt \
  --output-dir data/gallery \
  --gallery-version sample-gallery-v1 \
  --limit 100
```

## Planned Outputs

```text
data/gallery/
  gallery_embeddings.npy
  gallery_metadata.jsonl
  gallery_manifest.json
  gallery_build_report.json
```

Exact filenames may change, but the manifest is required.

## Build Steps
1. Validate dataset paths.
2. Load detector and embedder.
3. Read identity annotations.
4. Iterate sample images.
5. Detect one face per image.
6. Use the highest-scoring face if multiple are detected.
7. Align face.
8. Compute embedding.
9. Save embeddings and metadata.
10. Write manifest and build report.

## Runtime Rule
The runtime service loads gallery artifacts. It does not require raw CelebA images.
The current implementation can use a tiny local or test gallery artifact to validate search behavior.
Until the gallery exists, `/readyz` reports `gallery: not_loaded`.

## Skip Behavior
- No face detected: skip the image and record `no_face`.
- Decode failure: skip the image and record `decode_error`.
- Embedding failure: skip the image and record `embedding_failed`.
- Multiple faces: use the highest detection score and record `multiple_faces_used_best`.

## Failure Handling
Some images may fail detection or decoding. The builder must report:
- number attempted;
- number succeeded;
- number failed;
- failure reasons where practical.

The builder must fail clearly if the YuNet or SFace models are not loaded.

## Reproducibility
The build command and model versions must be documented. The manifest must include enough metadata to understand how the gallery was produced.

## MVP Shortcut
MVP may use a tiny synthetic or test gallery to validate API behavior. Full CelebA gallery build is required before RC1.
The repository uses a tiny fixture gallery for tests only; it is not a CelebA build.
The sample builder is intentionally not a full CelebA pipeline.
