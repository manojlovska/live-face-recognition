# AGENTS.md

## Mission
This repository implements a CPU-only, OpenAI-compatible face-similarity web service. The service accepts face images, detects and aligns faces, computes face embeddings, compares them against a versioned CelebA-derived embedding gallery, and returns the most similar CelebA identities.

The project must be professional-grade: reproducible, test-backed, privacy-conscious, documented, benchmarked, and honest about limitations.

## Product Promise
Users can call this service with OpenAI-style clients by setting a custom `base_url`, one API key, and the model name `celeba-face-similarity-cpu`. The result is a face-similarity result, not identity verification.

## Non-Negotiable Rules
- CPU-only: do not add CUDA, GPU-only, or GPU-required dependencies.
- Do not train a new deep model unless explicitly requested in a future architecture decision.
- Do not store uploaded user images by default.
- Do not store user face embeddings by default.
- Do not log base64 images, raw images, embeddings, Authorization headers, or API keys.
- Do not claim verified identity recognition.
- Do not claim commercial readiness for CelebA-backed operation unless licensing has been reviewed.
- Do not invent benchmark numbers, test results, gallery statistics, or CI status.
- Do not silently widen the API beyond the documented OpenAI-compatible subset.
- Do not add user accounts, PostgreSQL, Redis, Celery, Kubernetes, or frontend frameworks unless a scoped work order requests them.
- Do not merge your own pull request.

## Required First Reading
Before implementation work, read:
- `docs/project-brief.md`
- `docs/current-state.md`
- `docs/architecture.md`
- `docs/security.md`
- `docs/privacy.md`
- `docs/openai-compatibility.md`
- `docs/testing-strategy.md`
- `docs/release-readiness.md`

When changing model, dataset, gallery, or inference behavior, also read:
- `docs/model-card.md`
- `docs/dataset-and-licensing.md`
- `docs/gallery-build.md`
- `docs/gallery-manifest.md`

When changing browser, streaming, or live-frame behavior, also read:
- `docs/streaming-design.md`
- `docs/browser-demo-design.md`

When making a significant architecture decision, add or update an ADR in:
- `docs/architecture-decisions/`

## Architecture Summary
The intended architecture is:

```text
OpenAI client / native client / browser demo
        |
        v
FastAPI service
        |
        +-- one-key Bearer auth
        +-- OpenAI-compatible adapter: /v1/models, /v1/chat/completions
        +-- native API: /v1/face/similarity
        +-- readiness/health endpoints
        |
        v
Inference pipeline
        +-- image decode and validation
        +-- YuNet CPU face detection
        +-- SFace CPU face alignment and embedding
        +-- top-k similarity search against precomputed CelebA gallery
        |
        v
Gallery artifacts
        +-- embeddings file
        +-- metadata file
        +-- manifest file
```

## Approved Initial Stack
Use this stack unless a later approved ADR changes it:

- Python 3.11 or 3.12
- FastAPI
- Uvicorn
- Pydantic and pydantic-settings
- OpenCV headless/contrib package for YuNet/SFace support
- NumPy
- Pillow
- pytest, pytest-asyncio, pytest-cov
- httpx
- OpenAI Python SDK for compatibility tests/examples
- ruff and ruff format

Optional later dependencies must be justified in the PR:
- onnxruntime
- faiss-cpu
- pandas
- pyarrow
- orjson
- sse-starlette
- pre-commit
- pip-audit
- detect-secrets

## Repository Layout Target
Prefer this layout:

```text
app/
  main.py
  api/
  core/
  inference/
  gallery/
  openai_compat/
  schemas/
  static/
scripts/
  download_models.py
  build_gallery.py
  validate_gallery.py
  benchmark.py
tests/
  unit/
  integration/
  fixtures/
docs/
  ...
data/
  gallery/
    .gitkeep
models/
  .gitkeep
```

Generated model files, CelebA images, and large gallery artifacts should normally not be committed unless explicitly allowed. Commit manifests, examples, and tiny synthetic fixtures instead.

## API Rules
- `/healthz` returns process liveness.
- `/readyz` returns whether models and gallery artifacts are loaded.
- `/v1/models` returns at least `celeba-face-similarity-cpu`.
- `/v1/face/similarity` is the native API for direct image processing.
- `/v1/chat/completions` is the OpenAI-compatible API.
- OpenAI-compatible responses must be intentionally documented in `docs/openai-compatibility.md`.
- Unsupported OpenAI features must return clear structured errors, not fake LLM outputs.

## Security Rules
- The single API key must come from environment variable `FACE_API_KEY` or a documented equivalent.
- Require `Authorization: Bearer <key>` for protected endpoints.
- Never commit real keys or `.env` files containing secrets.
- Reject oversized images.
- Reject unsupported image types.
- Do not include raw images or embeddings in logs.
- If a secret appears in output, stop and report it.

## Privacy Rules
- Default retention is zero: process images in memory and discard them.
- Do not persist user images, user embeddings, or request bodies by default.
- Debug saving must be opt-in, clearly configured, documented, and disabled by default.
- The service output must include or preserve a disclaimer that results are similarity estimates, not identity verification.

## Dataset and Licensing Rules
- CelebA use must be described as research/demo unless legal clearance says otherwise.
- Return CelebA identity IDs by default.
- Do not invent celebrity display names.
- Add human-readable names only from a legally reviewed mapping.
- Keep dataset/model license notes current in `docs/dataset-and-licensing.md`.

## Testing Rules
Every PR must run relevant tests and report exact results.

At minimum for code changes:
- `ruff check .`
- `ruff format --check .`
- `pytest`

If a command is not run, say `not run` and explain why. A skipped or unavailable test is not a passing test.

Required test categories over time:
- auth success/failure
- health/readiness
- `/v1/models`
- image decoding and validation
- invalid image
- oversized image
- no-face image
- one-face image
- multi-face behavior
- gallery loading
- top-k similarity search
- OpenAI client compatibility
- streaming response behavior once implemented
- browser API behavior once implemented

## Documentation Update Rules
When changing API behavior, update:
- `docs/api.md`
- `docs/native-api.md`
- `docs/openai-compatibility.md`
- `docs/error-handling.md`

When changing model/gallery behavior, update:
- `docs/model-card.md`
- `docs/gallery-build.md`
- `docs/gallery-manifest.md`

When changing security, retention, or logging behavior, update:
- `docs/security.md`
- `docs/privacy.md`
- `docs/threat-model.md`

When changing release scope, update:
- `docs/roadmap.md`
- `docs/current-state.md`
- `docs/release-readiness.md`
- `docs/handoff.md`

When adding benchmarks, update:
- `docs/benchmark-results.md`

## Work Unit Rules
Use PR-sized work. One work order should produce one coherent branch and one reviewable PR.

Before editing:
- inspect current repository state;
- read relevant docs;
- confirm whether the work tree is clean;
- avoid unrelated formatting or refactors.

During implementation:
- keep changes scoped;
- use existing project patterns;
- add tests for behavior;
- update docs when behavior changes;
- do not broaden scope without explicit instruction.

Final report must include:

```text
Branch:
Commit:
Pull request:
Summary:
Files changed:
Tests run:
Documentation changed:
Local tools/dependencies installed:
Safety/privacy confirmations:
Known limitations:
Recommended follow-up:
```

## Release Language
Allowed wording before RC1:
- research prototype
- local CPU demo
- controlled pilot candidate
- face-similarity service
- similarity to CelebA identities

Forbidden wording unless separately approved:
- production biometric identification system
- verified celebrity recognition
- commercial CelebA service
- legally approved face recognition product
- 30 FPS real-time recognition guarantee

## Current MVP Target
The current MVP target is a CPU-only FastAPI service with:
- one-key auth;
- `/healthz` and `/readyz`;
- `/v1/models`;
- `/v1/face/similarity`;
- non-streaming `/v1/chat/completions`;
- YuNet/SFace inference path;
- small gallery support;
- OpenAI client example;
- tests and documentation.

## RC1 Target
RC1 means controlled-pilot-ready research service with:
- reproducible CelebA gallery workflow;
- OpenAI-compatible non-streaming and streaming response behavior;
- browser webcam demo with throttled frames;
- benchmark results;
- privacy/security/model documentation;
- passing tests/lint;
- honest release notes and limitations.
