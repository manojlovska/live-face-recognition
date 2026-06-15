# Deployment

## MVP Deployment Target
Local CPU machine or development VM.

## Environment Variables
Expected initial variables:

```text
FACE_API_KEY=change-me-local-dev-key
FACE_MODEL_ID=celeba-face-similarity-cpu
FACE_GALLERY_PATH=data/gallery
FACE_MAX_IMAGE_BYTES=...
FACE_MAX_IMAGE_PIXELS=...
```

Set `FACE_API_KEY` before starting the service so protected endpoints can reject missing or wrong credentials.

Exact variables must be updated once implementation exists.

## Local Run Target
Expected command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Health Checks
- `/healthz` for process liveness
- `/readyz` for model/gallery readiness

## Docker
Docker is recommended before RC1 but not required for MVP. If added, it must remain CPU-only and must not include CelebA raw data or secrets by default.

## Production Caution
Before internet exposure:
- enable HTTPS through reverse proxy;
- set request size limits at proxy and app layers;
- rotate API key;
- review privacy requirements;
- review dataset licensing;
- add monitoring/logging safeguards;
- run benchmarks and dependency audit.

## Not Included in MVP
- Kubernetes
- autoscaling
- multi-user auth
- managed database
- queue workers
- GPU deployment
