# Operator Runbook

This runbook is for a local operator preparing or validating a controlled pilot. It assumes the service remains CPU-only and similarity-focused.

## Local development start

```bash
pip install -e '.[dev,test]'
uvicorn app.main:app --reload
```

## Docker start without assets

```bash
docker run --rm \
  -p 8000:8000 \
  -e FACE_API_KEY=change-me-local-dev-key \
  live-face-recognition:local
```

## Docker start with model and gallery assets

```bash
docker run --rm \
  -p 8000:8000 \
  -e APP_ENV=production \
  -e STRICT_STARTUP_VALIDATION=true \
  -e FACE_API_KEY=change-me-production-key \
  -e MODEL_AUTO_LOAD=true \
  -e GALLERY_AUTO_LOAD=true \
  -v "$PWD/models:/app/models:ro" \
  -v "$PWD/data/gallery:/app/data/gallery:ro" \
  live-face-recognition:local
```

## Building a sample gallery

```bash
python scripts/build_gallery.py \
  --images-dir /path/to/sample/images \
  --identity-file /path/to/identity_sample.txt \
  --output-dir data/gallery \
  --gallery-version sample-gallery-v1 \
  --limit 100
```

## Building a local CelebA-style gallery

```bash
python scripts/build_gallery.py \
  --celeba-root /path/to/celeba \
  --output-dir data/gallery \
  --gallery-version celeba-local-v1 \
  --limit 1000 \
  --include-partitions train,val
```

## Checking readiness

```bash
curl http://127.0.0.1:8000/healthz
curl http://127.0.0.1:8000/readyz
```

## Reading startup diagnostics

```bash
curl -H "Authorization: Bearer $FACE_API_KEY" \
  http://127.0.0.1:8000/v1/diagnostics/startup
```

## Running smoke tests

```bash
python scripts/smoke_release.py --base-url http://localhost:8000 --api-key "$FACE_API_KEY" --check-diagnostics
```

Run this from the repository root; the script now resolves the project package path for direct execution.

## Running benchmarks

```bash
python scripts/benchmark_api.py --base-url http://localhost:8000 --api-key "$FACE_API_KEY" --endpoint all --requests 20
```

Run this from the repository root as well. When model or gallery assets are unavailable, the benchmark will still produce a measured `engine_not_ready` baseline that should not be treated as a pilot benchmark.
This repository state also records that the WO22 ready-path validation remains blocked without Docker and the real model/gallery assets.

## Using the native API

```bash
curl -H "Authorization: Bearer $FACE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"image":"data:image/jpeg;base64,...","top_k":5,"return_face_boxes":true}' \
  http://127.0.0.1:8000/v1/face/similarity
```

## Using OpenAI-compatible chat completions

```python
from openai import OpenAI

client = OpenAI(api_key="change-me-local-dev-key", base_url="http://localhost:8000/v1")
```

Use the documented `messages` payload with one `image_url` data URL.

## Using the browser demo

- Open `/demo`.
- Start the camera.
- Capture one frame or enable low-rate live polling.
- Stop live polling before closing the tab if needed.

## Common failure modes

- Missing `FACE_API_KEY`: protected routes return 401.
- Default local API key in production: startup validation fails.
- Missing YuNet model: `/readyz` stays not ready.
- Missing SFace model: `/readyz` stays not ready.
- Gallery missing: `/readyz` stays not ready.
- Gallery dimension mismatch: similarity requests fail with a structured error.
- Unsupported image type: native and chat endpoints reject the request.
- Camera permission denied in browser: the demo cannot start the preview.
- `/readyz` is 503 but `/healthz` is 200: the process is alive but the runtime is not ready for similarity results.
- Docker image built but assets not mounted: the container can start, but readiness remains not ready until model and gallery artifacts are provided.

## Safe shutdown and cleanup

- Stop live polling in the browser before closing the page.
- Stop the container with `Ctrl+C` or `docker stop`.
- Remove temporary local gallery artifacts only if they are no longer needed.
- Keep `.env`, generated reports, and any local secrets out of Git.
