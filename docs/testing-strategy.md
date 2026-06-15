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
| OpenAI compatibility | OpenAI Python client can call local `/v1/chat/completions` |

## RC1 Test Categories
- response streaming with `stream=true`;
- repeated-frame processing behavior;
- browser demo API path;
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
- native similarity tests that still return `engine_not_ready` when YuNet is unavailable.

## Test Quality Rule
For every important safety behavior, ask:

> If the dangerous behavior regressed, would this test fail?
