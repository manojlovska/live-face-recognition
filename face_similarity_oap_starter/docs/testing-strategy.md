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
| Models | `/v1/models` returns expected model ID |
| Image validation | accepts valid image and rejects invalid/oversized image |
| Native API | `/v1/face/similarity` returns structured result |
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

## Test Quality Rule
For every important safety behavior, ask:

> If the dangerous behavior regressed, would this test fail?
