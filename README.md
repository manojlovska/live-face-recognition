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

## Quality checks

```bash
ruff check .
ruff format --check .
pytest
```

## Environment

Copy `.env.example` to `.env` if you want to override defaults locally.

Project documentation lives under `face_similarity_oap_starter/docs/`.
