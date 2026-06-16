# Testing Strategy

## Testing Goal
Tests must prove behavior, not merely exercise code. A passing test is evidence only for the claim it covers.

## Required Commands
For most PRs:

```bash
ruff check .
ruff format --check .
pytest
```

If a command is not run, report it as `not run` with the reason.

## MVP Test Categories

| Category | Required behavior |
|---|---|
| Config | loads required settings and rejects missing required config when appropriate |
| Auth | missing/wrong/correct API key paths |
| Health | `/healthz` works without model readiness |
| Readiness | `/readyz` reflects model/gallery load state |
| Models | `/v1/models` returns expected model ID and remains protected |
| Native API | `/v1/face/similarity` enforces contract and reports engine-not-ready |
| Image validation | accepts valid JPEG/PNG/WebP data URLs and rejects malformed/unsupported/oversized/non-image payloads |
| Request validation | accepts valid JSON contract and rejects invalid `top_k`/missing fields |
| No-face | no-face behavior is deterministic and documented |
| Gallery | gallery loads and top-k search is deterministic on fixtures |
| Gallery builder | sample-gallery build is deterministic on tiny fixtures |
| OpenAI compatibility | OpenAI Python client can call local `/v1/chat/completions` |

## RC1 Test Categories
- response streaming with `stream=true`;
- repeated-frame processing behavior;
- browser demo API path;
- browser demo live polling behavior;
- release smoke-test script behavior;
- benchmark script smoke test;
- Docker packaging checks for CPU-only runtime, non-root user, and ignore rules;
- smoke-script container target checks against `/healthz`, `/readyz`, native API, chat API, and `/demo`;
- privacy no-retention default;
- security scan or secret-pattern check;
- error object compatibility.

## Warning Policy
- The previous `StarletteDeprecationWarning` came from the Starlette/FastAPI TestClient fallback to `httpx`.
- The test dependency set now installs `httpx2`, so `fastapi.testclient.TestClient` takes the non-deprecated Starlette path.
- Release-candidate runs should fail on warnings with `python3.12 -m pytest -W error`.
- If a future warning must be filtered, it should be a narrow, documented exception rather than a blanket ignore.

## Dependency Policy
- Runtime dependencies are bounded for CPU-only release-candidate use.
- Local scripts use `httpx` from the `dev` extra.
- Tests use the `test` extra, which provides `httpx2`, `openai`, and pytest tooling.
- No GPU, database, Redis, Celery, or frontend build dependencies are included.

## Release-Candidate Pass
Install the local development and test extras, then run the strict release-candidate test pass:

```bash
pip install -e '.[dev,test]'
python3.12 -m pytest -W error
```

Use the normal lint/test commands as well:

```bash
python3.12 -m ruff check .
python3.12 -m ruff format --check .
python3.12 -m pytest
```

## Fixtures
Use tiny synthetic or legally safe fixtures. Do not commit CelebA images unless the repository policy explicitly permits it.

## Model Tests
Where real model files are unavailable in CI, tests should distinguish:
- unit tests using stub inference;
- integration tests requiring model files;
- full gallery tests requiring local dataset/artifacts.

Skipped integration tests must be reported as skipped, not passed.

## Current Model Work Coverage
- model asset manager checksum and presence tests;
- CPU-only loader skeleton tests with stubbed OpenCV objects;
- readiness tests for missing and present-but-not-loaded model files;
- native similarity tests for detector-missing, detection-only, and no-face responses;
- native similarity tests for embedding-only responses, per-face embedding metadata, and raw-vector privacy;
- native similarity tests that still return `engine_not_ready` when YuNet is unavailable.
- gallery artifact loading tests for manifest, metadata, dimension, and checksum validation;
- gallery search tests for deterministic cosine top-k ranking on the tiny fixture gallery;
- readiness tests for loaded-gallery and gallery-error states.
- CelebA annotation parsing tests for comments, blank lines, and malformed rows;
- CelebA layout discovery tests for flat and nested `img_align_celeba/` layouts;
- CelebA partition parsing tests for `train`, `val`, and `test` mapping;
- gallery builder tests for writes, skips, multiple-face handling, runtime readiness checks, and reporting;
- script tests for dry-run, missing input, existing output, and successful sample builds.
- OpenAI chat-completions tests for HTTP contract coverage, native error passthrough, and Python client compatibility against a local `base_url`.
- OpenAI chat-completions streaming tests for SSE chunk shape, `[DONE]`, and Python client streaming compatibility against a local `base_url`.
- Browser demo tests for `/demo`, local static assets, and no-storage/no-CDN script checks.
- Browser overlay tests for optional face-box drawing logic, local canvas usage, and no continuous polling indicators.
- Browser demo live-polling tests for start/stop controls, single-flight request guards, polling interval handling, hidden-tab stop behavior, and same-origin native API usage.
- Release smoke-test tests for generated image data URLs, readiness classification, auth checks, demo-page checks, and redacted output.
- Benchmark script tests for latency summaries, status counts, result-mode extraction, CLI parsing, and JSON report writing.
- Docker packaging tests for a CPU-only image, non-root runtime user, and build-context exclusions.
- Dependency-policy tests for bounded runtime/test extras, no forbidden GPU packages, and a warning-free Starlette TestClient import path.

## Test Quality Rule
For every important safety behavior, ask:

> If the dangerous behavior regressed, would this test fail?
