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

## Authentication

Future protected endpoints will require:

```http
Authorization: Bearer <FACE_API_KEY>
```

Set `FACE_API_KEY` locally in `.env` before using protected routes.

```bash
export FACE_API_KEY="change-me-local-dev-key"
# Future protected endpoints will use:
# curl -H "Authorization: Bearer $FACE_API_KEY" http://127.0.0.1:8000/...
```

## Quality checks

```bash
ruff check .
ruff format --check .
pytest
```

## Environment

Copy `.env.example` to `.env` if you want to override defaults locally.

Project documentation lives under `docs/`.
