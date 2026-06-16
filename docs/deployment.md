# Deployment

## MVP Deployment Target
Local CPU machine, development VM, or a local container.

## Local Python Run

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

This is the simplest development path and keeps model/gallery files on the host filesystem.

For development, the default mode is intentionally forgiving:

- `APP_ENV=development`
- `STRICT_STARTUP_VALIDATION=false`
- `STARTUP_VALIDATE_ASSETS=true`
- `DIAGNOSTICS_INCLUDE_PATHS=false`
- `DEBUG_IMAGE_RETENTION=false`

## Docker Build

```bash
docker build -t live-face-recognition:local .
```

The image is CPU-only and does not bake in model files, gallery artifacts, reports, API keys, or `.env`.

## Docker Run Without Local Assets

The container can start without mounted model or gallery artifacts. In that case `/healthz` should still return `200`, while `/readyz` may legitimately return `503 not_ready`.

```bash
docker run --rm \
  -p 8000:8000 \
  -e FACE_API_KEY=change-me-local-dev-key \
  live-face-recognition:local
```

## Docker Run With Mounted Assets

Mount model and gallery artifacts read-only for serving:

```bash
docker run --rm \
  -p 8000:8000 \
  -e FACE_API_KEY=change-me-local-dev-key \
  -e MODEL_AUTO_LOAD=true \
  -e GALLERY_AUTO_LOAD=true \
  -v "$PWD/models:/app/models:ro" \
  -v "$PWD/data/gallery:/app/data/gallery:ro" \
  live-face-recognition:local
```

If you want to write reports from inside a containerized workflow, mount `reports/` separately and only for that workflow:

```bash
docker run --rm \
  -p 8000:8000 \
  -e FACE_API_KEY=change-me-local-dev-key \
  -v "$PWD/reports:/app/reports" \
  live-face-recognition:local
```

The API container itself does not need write access to `reports/` during normal serving.

## Production-Like Run

Use explicit production settings when you want fail-fast validation:

```bash
docker run --rm \
  -p 8000:8000 \
  -e APP_ENV=production \
  -e STRICT_STARTUP_VALIDATION=true \
  -e STARTUP_VALIDATE_ASSETS=true \
  -e FACE_API_KEY=change-me-production-key \
  -v "$PWD/models:/app/models:ro" \
  -v "$PWD/data/gallery:/app/data/gallery:ro" \
  live-face-recognition:local
```

If the API key is the default local placeholder, if `DEBUG_IMAGE_RETENTION=true`, or if startup validation is disabled in production, startup diagnostics will report errors and the application will fail fast.

## Environment Variables

The main runtime variables are:

```text
APP_ENV=development
STRICT_STARTUP_VALIDATION=false
STARTUP_VALIDATE_ASSETS=true
DIAGNOSTICS_INCLUDE_PATHS=false
DEBUG_IMAGE_RETENTION=false
FACE_API_KEY=change-me-local-dev-key
FACE_MODEL_ID=celeba-face-similarity-cpu
MODEL_ASSET_DIR=models
YUNET_MODEL_PATH=models/face_detection_yunet.onnx
SFACE_MODEL_PATH=models/face_recognition_sface.onnx
MODEL_MANIFEST_PATH=models/model_manifest.json
MODEL_AUTO_LOAD=false
GALLERY_DIR=data/gallery
GALLERY_EMBEDDINGS_PATH=data/gallery/gallery_embeddings.npy
GALLERY_METADATA_PATH=data/gallery/gallery_metadata.jsonl
GALLERY_MANIFEST_PATH=data/gallery/gallery_manifest.json
GALLERY_AUTO_LOAD=false
FACE_MAX_IMAGE_BYTES=5242880
```

Set `FACE_API_KEY` before starting the service so protected endpoints can reject missing or wrong credentials.

## Startup Diagnostics

The protected `GET /v1/diagnostics/startup` endpoint reports sanitized startup diagnostics.
It is useful for local and container startup checks, and it can optionally include selected paths only when `DIAGNOSTICS_INCLUDE_PATHS=true`.

Example:

```bash
curl -H "Authorization: Bearer $FACE_API_KEY" \
  http://localhost:8000/v1/diagnostics/startup
```

## Healthcheck and Readiness

- `/healthz` reports process liveness and is appropriate for container healthchecks.
- `/readyz` reports model/gallery readiness and may return `503 not_ready` when local assets are absent.
- A container can be healthy while still not ready for similarity results.

## Smoke Test Against Container

Run the existing host-side smoke script against the container:

```bash
python scripts/smoke_release.py \
  --base-url http://localhost:8000 \
  --api-key change-me-local-dev-key \
  --output reports/smoke-container.json
```

## Production Caution

Before internet exposure:
- enable HTTPS through a reverse proxy or orchestrator;
- set request size limits at proxy and app layers;
- rotate the API key;
- review privacy requirements;
- review dataset licensing;
- add monitoring/logging safeguards;
- run benchmarks and dependency audit;
- keep model and gallery mounts read-only for serving.

## Not Included

- Kubernetes
- autoscaling
- multi-user auth
- managed database
- queue workers
- GPU deployment
