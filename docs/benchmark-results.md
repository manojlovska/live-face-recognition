# Benchmark Results

## Status
A dated RC validation baseline is recorded below, along with a ready-path validation run from a Docker-capable machine with mounted models and a small local gallery. These are local validation results, not a final commercial benchmark claim.

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

## RC ready-path validation run: 2026-06-16

### Environment

- Operator: Codex
- Machine/CPU: Intel(R) Core(TM) Ultra 7 165H, 22 logical CPUs
- RAM: 15 GiB
- OS: Linux 6.18.33.1-microsoft-standard-WSL2 on WSL2
- Python: Python 3.12.3
- Docker: Docker 29.1.3, build 29.1.3-0ubuntu3~24.04.2
- Image tag: `live-face-recognition:rc-ready`
- Git commit: `feature/wo-024r-sudo-ready-path-validation` working tree
- Model assets: `models/face_detection_yunet.onnx` and `models/face_recognition_sface.onnx` downloaded locally from OpenCV Zoo; SHA-256 computed locally
- Gallery version: `rc-ready-small-gallery-v1`
- Gallery item count: 10
- Gallery embedding dimension: 128

### Validation summary

| Check | Result | Notes |
|---|---|---|
| Clean install | pass | `python3.12 -m venv .venv`, `python -m pip install -e '.[dev,test]'` succeeded. |
| Ruff check | pass | `python -m ruff check .` |
| Ruff format check | pass | `python -m ruff format --check .` |
| Pytest -W error | pass | `python -m pytest -W error` passed with 167 tests. |
| Docker build | pass | `sudo docker build -t live-face-recognition:rc-ready .` |
| Smoke without assets | pass | Container started operational-but-not-ready; smoke returned `not_ready` with sanitized diagnostics. |
| Gallery build | pass | Small local gallery built from 10 permitted sample images and 2 identities. |
| Smoke with assets | pass | Container returned `ready` with sanitized diagnostics. |
| Readyz with assets | pass | `/readyz` returned `200 ready`. |

### Benchmark results

| Endpoint | Requests | Warmup | Result mode | Min ms | Mean ms | Median ms | P95 ms | Max ms | Errors |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| native | 20 | 3 | similarity | 76.267 | 92.756 | 93.607 | 103.230 | 106.154 | 0 |
| chat | 20 | 3 | similarity | 78.909 | 94.117 | 93.524 | 102.506 | 107.238 | 0 |
| chat-stream | 20 | 3 | similarity | 91.662 | 104.155 | 103.746 | 109.597 | 112.402 | 0 |

### Stream timing

- chat-stream first chunk latency: min 90.380 ms, mean 102.804 ms, median 102.278 ms, p95 108.694 ms, max 110.332 ms.

### Notes and blockers

- A second ready-path benchmark using the generated 1x1 image also returned `similarity` results with lower latencies, but the representative-image run above is the primary ready-path measurement.
- The validation run used a small local gallery, not the full CelebA workflow.
- Dataset/legal review is still required before any external or commercial use.
- No API keys, raw embeddings, or base64 image payloads were recorded in the report files.

## Current RC1 Limitation
Authoritative pilot use still requires dataset/legal review and, if the release target differs from this local validation environment, a final run on the target machine with the same assets.
