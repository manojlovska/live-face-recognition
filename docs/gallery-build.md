# Gallery Build

## Purpose
The runtime service must not scan CelebA images at request time. Instead, an offline build process creates gallery artifacts used by the runtime service.
The runtime gallery loader is implemented now. The builder supports a small explicit sample directory and a CelebA-style local layout, but the full CelebA dataset workflow remains future work.

## Builder Modes

### Explicit sample mode

Use explicit paths when building a small sample gallery or a test fixture:

```bash
python scripts/build_gallery.py \
  --images-dir /path/to/sample/images \
  --identity-file /path/to/identity_sample.txt \
  --output-dir data/gallery \
  --gallery-version sample-gallery-v1 \
  --limit 100
```

### CelebA-root mode

Use `--celeba-root` when the local dataset follows the common CelebA layout:

```bash
python scripts/build_gallery.py \
  --celeba-root /path/to/celeba \
  --output-dir data/gallery \
  --gallery-version celeba-local-v1 \
  --limit 1000 \
  --include-partitions train,val
```

The builder discovers:
- `img_align_celeba/`
- nested `img_align_celeba/img_align_celeba/`
- `identity_CelebA.txt`
- optional `list_eval_partition.txt`

## Inputs
- Local image directory or CelebA root directory
- CelebA-style identity annotation file with `image_filename identity_id` rows
- Optional CelebA-style partition file with `image_filename partition_id` rows
- YuNet model file
- SFace model file

## Output Artifacts

```text
data/gallery/
  gallery_embeddings.npy
  gallery_metadata.jsonl
  gallery_manifest.json
  gallery_build_report.json
```

The manifest is required. The build report is generated output and is normally not committed.

## Output Collision Behavior
- Without `--overwrite`, the builder rejects an output directory that already contains gallery artifacts.
- With `--overwrite`, the builder may replace existing local gallery artifacts.
- The builder never writes outside `--output-dir`.

## Build Steps
1. Validate dataset paths or discover the CelebA root layout.
2. Load detector and embedder.
3. Read identity annotations.
4. Optionally read partition annotations and filter by partition.
5. Apply `--start-after` and `--limit` after filtering.
6. Iterate the selected images.
7. Detect one face per image.
8. Use the highest-scoring face if multiple are detected.
9. Skip low-score detections according to `--min-det-score`.
10. Align face and compute embedding.
11. Save embeddings and metadata.
12. Write manifest and build report with quality and timing summaries.

## Skip Behavior
- No face detected: skip the image and record `no_face`.
- Decode failure: skip the image and record `decode_error`.
- Low detection score: skip the image and record `low_detection_score`.
- Embedding failure: skip the image and record `embedding_failed`.
- Multiple faces: use the highest detection score and record `multiple_faces_used_best`.

## Reporting

### Quality report
`gallery_build_report.json` includes:
- `attempted`
- `succeeded`
- `skipped`
- `skip_reasons`
- `warnings`
- `quality`

`quality` may include:
- `success_rate`
- `identity_count`
- `min_detection_score`
- `mean_detection_score`
- `median_detection_score`

### Performance report
`gallery_build_report.json` also includes:
- `started_at`
- `finished_at`
- `duration_seconds`
- `images_per_second`
- `mean_image_seconds`

If a statistic is unavailable, it may be `null` instead of being invented.

## Failure Handling
The builder must fail clearly if the YuNet or SFace models are not loaded.
It must also fail clearly when the input layout is missing, malformed, or inconsistent.

## Reproducibility
The build command, layout mode, and model versions must be documented. The manifest must include enough metadata to understand how the gallery was produced.

## Scope Boundary
This builder is sample- and local-layout-oriented. It does not download CelebA and it does not claim a full CelebA-scale workflow yet.
