# Live Face Similarity API

## What this is

CPU-only FastAPI service for face similarity against a local CelebA-style gallery.
It supports a native JSON API, a minimal OpenAI-compatible adapter, a local browser demo, smoke tests, benchmarks, and Docker packaging.

## What this is not

- verified identity recognition
- commercial-ready biometric product
- cloud deployment system
- server-side video streaming
- WebSocket-based webcam service

The public APIs return similarity results, not identity proof.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev,test]'
uvicorn app.main:app --reload
```

## API overview

- `GET /healthz`
- `GET /readyz`
- `GET /v1/models`
- `POST /v1/face/similarity`
- `POST /v1/chat/completions`
- `GET /v1/diagnostics/startup`

See [docs/api.md](docs/api.md), [docs/native-api.md](docs/native-api.md), and [docs/openai-compatibility.md](docs/openai-compatibility.md).

## OpenAI-compatible usage

```python
from openai import OpenAI

client = OpenAI(api_key="change-me-local-dev-key", base_url="http://localhost:8000/v1")
```

See [docs/openai-compatibility.md](docs/openai-compatibility.md) for the supported image-only subset.

## Browser demo

The local demo at `/demo` supports one-frame capture, optional face-box overlays, and opt-in low-rate live polling.
See [docs/browser-demo-design.md](docs/browser-demo-design.md).

## Gallery builder

Use the local builder to create a sample gallery or a CelebA-style local gallery:

```bash
python scripts/build_gallery.py --images-dir /path/to/sample/images --identity-file /path/to/identity_sample.txt --output-dir data/gallery --gallery-version sample-gallery-v1 --limit 100
python scripts/build_gallery.py --celeba-root /path/to/celeba --output-dir data/gallery --gallery-version celeba-local-v1 --limit 1000 --include-partitions train,val
```

See [docs/gallery-build.md](docs/gallery-build.md) and [docs/gallery-manifest.md](docs/gallery-manifest.md).

## Docker

```bash
docker build -t live-face-recognition:local .
docker run --rm -p 8000:8000 -e FACE_API_KEY=change-me-local-dev-key live-face-recognition:local
```

Model and gallery artifacts are mounted at runtime. See [docs/deployment.md](docs/deployment.md).

## Smoke tests and benchmarks

```bash
python scripts/smoke_release.py --base-url http://localhost:8000 --api-key change-me-local-dev-key --check-diagnostics
python scripts/benchmark_api.py --base-url http://localhost:8000 --api-key change-me-local-dev-key --endpoint all --requests 20
```

See [docs/release-readiness.md](docs/release-readiness.md), [docs/pilot-readiness-checklist.md](docs/pilot-readiness-checklist.md), [docs/operator-runbook.md](docs/operator-runbook.md), and [docs/benchmark-plan.md](docs/benchmark-plan.md).

## Privacy and security

- API keys are not stored.
- Uploaded images are not stored by default.
- User embeddings are not stored by default.
- Startup diagnostics are sanitized.

See [docs/security.md](docs/security.md) and [docs/privacy.md](docs/privacy.md).

## Dataset and licensing

The intended gallery base is CelebA, but local dataset use and any broader use must be reviewed carefully.
See [docs/dataset-and-licensing.md](docs/dataset-and-licensing.md) and [docs/model-card.md](docs/model-card.md).

## Documentation map

- [docs/current-state.md](docs/current-state.md)
- [docs/handoff.md](docs/handoff.md)
- [docs/release-readiness.md](docs/release-readiness.md)
- [docs/pilot-readiness-checklist.md](docs/pilot-readiness-checklist.md)
- [docs/operator-runbook.md](docs/operator-runbook.md)
- [docs/release-notes-rc1.md](docs/release-notes-rc1.md)
- [docs/testing-strategy.md](docs/testing-strategy.md)
- [docs/error-handling.md](docs/error-handling.md)
- [docs/benchmark-results.md](docs/benchmark-results.md)

## RC1 release package

These docs are for RC1 candidate review only and do not imply a final release.
This package does not imply a final release.

- [docs/github-release-draft-v0.1.0-rc1.md](docs/github-release-draft-v0.1.0-rc1.md)
- [docs/internal-rc1-announcement.md](docs/internal-rc1-announcement.md)
- [docs/rc1-human-approval-notes.md](docs/rc1-human-approval-notes.md)
- [docs/rc1-release-checklist.md](docs/rc1-release-checklist.md)
- [docs/rc1-release-manifest.md](docs/rc1-release-manifest.md)
- [docs/release-notes-rc1.md](docs/release-notes-rc1.md)
