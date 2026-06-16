# Pilot Operator Onboarding

## Audience

Pilot operators preparing a controlled RC1 run of the CPU-only face-similarity service.

## Scope of RC1

`v0.1.0-rc1` is a controlled release candidate for face similarity over a local gallery.
It is not identity verification.
It is not a final release.

## What RC1 does

- Serves a CPU-only FastAPI API.
- Accepts authenticated similarity requests.
- Supports OpenAI-compatible image-only chat completions.
- Provides `/healthz`, `/readyz`, and `/v1/diagnostics/startup`.
- Supports a local browser demo at `/demo`.

## What RC1 does not do

- It does not bundle ONNX model files.
- It does not bundle CelebA data.
- It does not bundle gallery artifacts.
- It does not provide identity verification.
- It does not provide commercial-readiness guarantees.

## Required local assets

- `models/face_detection_yunet.onnx`
- `models/face_recognition_sface.onnx`
- A local gallery under `data/gallery/`
- Authorized sample images if you need to build or refresh the gallery locally

Operators must supply authorized model and gallery assets locally.

## Required environment

- Python 3.12
- Docker
- `FACE_API_KEY`
- `APP_ENV`
- `MODEL_AUTO_LOAD=true` when using mounted model artifacts
- `GALLERY_AUTO_LOAD=true` when using mounted gallery artifacts

## Setup steps

1. Set `FACE_API_KEY` to a non-default secret value.
2. Mount `models/` and `data/gallery/` read-only when serving.
3. Use `APP_ENV=production` for pilot-like runs.
4. Keep `STRICT_STARTUP_VALIDATION=true` when you want fail-fast asset checks.
5. Confirm `/v1/diagnostics/startup` is sanitized.

## Running with Docker

```bash
docker run --rm \
  -p 8000:8000 \
  -e FACE_API_KEY="$FACE_API_KEY" \
  -e APP_ENV=production \
  -e STRICT_STARTUP_VALIDATION=true \
  -e MODEL_AUTO_LOAD=true \
  -e GALLERY_AUTO_LOAD=true \
  -v "$PWD/models:/app/models:ro" \
  -v "$PWD/data/gallery:/app/data/gallery:ro" \
  live-face-recognition:rc1
```

## Building or mounting a gallery

Build a sample gallery:

```bash
python scripts/build_gallery.py \
  --images-dir /path/to/sample/images \
  --identity-file /path/to/identity_sample.txt \
  --output-dir data/gallery \
  --gallery-version sample-gallery-v1 \
  --limit 100
```

Mount an existing gallery by pointing `data/gallery/` at the operator-managed artifact directory.

## Smoke test

```bash
python scripts/smoke_release.py \
  --base-url http://localhost:8000 \
  --api-key "$FACE_API_KEY" \
  --check-diagnostics
```

`/healthz` reports process liveness.
`/readyz` reports whether the detector, embedder, and gallery are loaded.

## Benchmark check

```bash
python scripts/benchmark_api.py \
  --base-url http://localhost:8000 \
  --api-key "$FACE_API_KEY" \
  --endpoint all \
  --requests 20 \
  --warmup 3 \
  --image-file /path/to/representative/image.jpg
```

Use a representative face image to measure the ready similarity path.

## Browser demo

- Open `/demo` in a browser.
- Grant camera permission when prompted.
- Capture one frame or use low-rate live polling.

## OpenAI-compatible client usage

```python
from openai import OpenAI

client = OpenAI(api_key="change-me-local-dev-key", base_url="http://localhost:8000/v1")
```

Use the documented image-only `messages` payload and a custom model name from the RC1 docs.

## Privacy and security expectations

- Do not store uploaded images by default.
- Do not store user embeddings by default.
- Do not log Authorization headers, API keys, raw images, base64 payloads, or embeddings.
- Keep diagnostics sanitized.

## Dataset/legal constraints

- RC1 is a face-similarity research/pilot candidate.
- Broader or external use must follow the approved scope and dataset/legal conditions.
- The service does not claim identity verification.
- The service does not claim commercial readiness beyond the approved RC1 scope.

## Troubleshooting

- Missing API key: protected endpoints return 401.
- Default key in production: startup validation fails.
- Missing model files: `/readyz` stays 503.
- Gallery missing: `/readyz` stays 503.
- Gallery dimension mismatch: similarity requests fail with a structured error.
- Camera permission denied: `/demo` cannot start the preview.
- `/healthz` 200 but `/readyz` 503: the process is alive but the runtime is not ready.
- Docker image built but assets not mounted: the container starts, but readiness remains not ready.

## Escalation checklist

- Confirm the exact `APP_ENV`, `STRICT_STARTUP_VALIDATION`, `MODEL_AUTO_LOAD`, and `GALLERY_AUTO_LOAD` values.
- Confirm the mounted paths for `models/` and `data/gallery/`.
- Confirm the gallery embedding dimension matches the model output dimension.
- Confirm the pilot scope and any dataset/legal conditions before broader use.
