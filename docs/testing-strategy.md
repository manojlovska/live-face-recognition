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
- benchmark script smoke test;
- privacy no-retention default;
- security scan or secret-pattern check;
- error object compatibility.

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

## Test Quality Rule
For every important safety behavior, ask:

> If the dangerous behavior regressed, would this test fail?
