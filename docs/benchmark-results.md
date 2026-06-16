# Benchmark Results

## Status
A dated RC validation baseline is recorded below. It is not yet an authoritative pilot benchmark because Docker and the real model/gallery assets were unavailable in this environment.

## Rule
Do not invent performance numbers. Add results only from actual benchmark runs.

## RC validation run: 2026-06-16

### Environment

- Operator: Codex
- Machine/CPU: Intel(R) Core(TM) Ultra 7 165H, 22 logical CPUs
- RAM: 15 GiB
- OS: Linux 6.18.33.1-microsoft-standard-WSL2 on WSL2
- Python: Python 3.12.3
- Docker: unavailable in this environment
- Image tag: not built
- Git commit: 28456bd working tree with WO21 validation changes
- Model assets: unavailable locally
- Gallery version: unavailable locally
- Gallery item count: 0
- Gallery embedding dimension: unavailable

### Validation summary

| Check | Result | Notes |
|---|---|---|
| Clean install | pass | `python3.12 -m pip install --break-system-packages -e '.[dev,test]'` succeeded; a fresh venv could not be created because this Python build lacks `ensurepip`. |
| Ruff check | pass | `python3.12 -m ruff check .` |
| Ruff format check | pass | `python3.12 -m ruff format --check .` |
| Pytest -W error | pass | `python3.12 -m pytest -W error` passed with 167 tests. |
| Docker build | not run | Docker CLI/daemon are unavailable in this environment. |
| Smoke without assets | pass | Local dev server returned the expected `not_ready` baseline and sanitized diagnostics. |
| Gallery build | not run | Local sample gallery inputs were unavailable. |
| Smoke with assets | not run | Model/gallery assets and Docker validation were unavailable. |
| Readyz with assets | not run | Model/gallery assets were unavailable. |

### Benchmark results

| Endpoint | Requests | Warmup | Result mode | Min ms | Mean ms | Median ms | P95 ms | Max ms | Errors |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| native | 20 | 3 | engine_not_ready | 1.030 | 1.645 | 1.593 | 2.440 | 2.643 | 0 |
| chat | 20 | 3 | engine_not_ready | 0.974 | 1.140 | 1.071 | 1.418 | 1.522 | 0 |
| chat-stream | 20 | 3 | engine_not_ready | 1.033 | 1.165 | 1.143 | 1.263 | 1.463 | 0 |

### Stream timing

- chat-stream first chunk latency: min 1.003 ms, mean 1.125 ms, median 1.101 ms, p95 1.219 ms, max 1.427 ms.

### Notes and blockers

- `engine_not_ready` is the expected outcome for this local baseline because the real YuNet/SFace model files were unavailable.
- Docker validation remains blocked because the Docker CLI/daemon are unavailable here.
- Gallery validation remains blocked because no real gallery artifacts were available to mount or load.
- These measurements are useful as a local error-path baseline, but they are not authoritative RC benchmark results for a pilot target.
- No API keys, raw embeddings, or base64 image payloads were recorded in the report files.

## Current RC1 Blocker
Authoritative RC benchmark results still require a Docker-capable machine with real model assets and a small local gallery.
