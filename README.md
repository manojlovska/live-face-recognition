# CelebA Face Similarity API

CPU-only FastAPI scaffold for the CelebA face-similarity service.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

## Run the app

```bash
uvicorn app.main:app --reload
```

## Health check

```bash
curl http://127.0.0.1:8000/healthz
```

`/healthz` is a public liveness check. It only reports that the process is up.

## Readiness check

```bash
curl http://127.0.0.1:8000/readyz
```

`/readyz` is public too, but it currently returns `503 not_ready` until models and gallery loading exist.
The response now includes model-asset status so you can tell whether YuNet and SFace files are missing, present, loaded, or in error.

## Authentication

Protected endpoints require:

```http
Authorization: Bearer <FACE_API_KEY>
```

Set `FACE_API_KEY` locally in `.env` before using protected routes.

```bash
export FACE_API_KEY="change-me-local-dev-key"
# Current and future protected endpoints use:
# curl -H "Authorization: Bearer $FACE_API_KEY" http://127.0.0.1:8000/...
```

## Model list

```bash
curl -H "Authorization: Bearer change-me-local-dev-key" \
  http://localhost:8000/v1/models
```

`/v1/models` is protected and lists the configured model ID. The similarity engine is still not ready.

## Native similarity

Valid `POST /v1/face/similarity` image requests are decoded and validated in memory. If YuNet is loaded, the service returns detection-only face boxes. Similarity matching is still not implemented.

Model files are expected under `models/` by default:

- `models/face_detection_yunet.onnx`
- `models/face_recognition_sface.onnx`
- `models/model_manifest.json`

To test real YuNet detection manually:

1. Place the YuNet ONNX file at the configured `YUNET_MODEL_PATH`.
2. Set `MODEL_AUTO_LOAD=true`.
3. Start the server.
4. Send a valid `POST /v1/face/similarity` request.
5. A detection-only result should be returned when the detector loads successfully.

## Quality checks

```bash
ruff check .
ruff format --check .
pytest
```

## Environment

Copy `.env.example` to `.env` if you want to override defaults locally.

Project documentation lives under `docs/`.
