# Release Readiness

## Release Principle
Feature completion is not release readiness. Release readiness requires evidence: tests, docs, benchmark results, privacy/security review, and honest limitations.
This repository is ready for a controlled pilot only after the pilot checklist is completed.

## WO21 Validation Status

- Warning-free `ruff` and `pytest -W error` passes were reproduced locally.
- The smoke script ran directly from the repository root against a local development server and reported the expected `not_ready` baseline because the real model/gallery assets were unavailable.
- The benchmark script measured a local `engine_not_ready` baseline for native, chat, and chat-stream paths.
- Docker validation is blocked in this environment because the Docker CLI/daemon is unavailable.
- Real model/gallery RC validation is blocked in this environment because the required assets are unavailable locally.
- This worktree is not ready for a controlled pilot yet.

## Release Documents

- [Pilot readiness checklist](pilot-readiness-checklist.md)
- [Operator runbook](operator-runbook.md)
- [RC1 release notes draft](release-notes-rc1.md)
- [Benchmark plan](benchmark-plan.md)
- [Benchmark results](benchmark-results.md)
- [Dataset and licensing](dataset-and-licensing.md)

## MVP Gates

| Gate | Required evidence | Status |
|---|---|---|
| Install | documented local install works | not started |
| Auth | one-key auth tested | in progress |
| Health | `/healthz` tested | in progress |
| Readiness | `/readyz` tested | in progress |
| Models | `/v1/models` tested | in progress |
| Native API | `/v1/face/similarity` tested | in progress |
| OpenAI API | non-streaming `/v1/chat/completions` works | complete |
| CPU inference | YuNet detection and internal SFace embeddings work without GPU | in progress |
| Gallery | small gallery works | complete |
| Privacy | no image/embedding retention by default | not started |
| Docs | README and core docs updated | in progress |
| Tests | warning-free `pytest`, `ruff check`, and `pytest -W error` pass | in progress |

## RC1 Gates

| Gate | Required evidence | Status |
|---|---|---|
| Full gallery | reproducible CelebA gallery workflow | not started |
| Streaming | OpenAI-style `stream=true` works | complete |
| Live frames | repeated-frame API tested | not started |
| Browser demo | HTML5 webcam demo works | complete |
| Benchmarks | CPU benchmark results documented | not started |
| Security | auth, request limits, no-secret checks | not started |
| Privacy | no-retention policy documented and tested where practical | not started |
| Packaging | CPU-only Docker image and container smoke checks | in progress |
| Configuration | startup validation and sanitized diagnostics | in progress |
| Dependencies | runtime/test dependency bounds reviewed for CPU-only RC use | in progress |
| Model card | complete and honest | initial draft |
| Dataset licensing | limitations documented | initial draft |
| Error handling | structured errors documented/tested | in progress |
| Compatibility | OpenAI Python client compatibility test | complete |
| Release language | no overclaims | in progress |

## RC1 Allowed Claim
Controlled-pilot-ready CPU-only research service for CelebA-based face similarity.

The API now supports detector-only, embedding-only, and gallery-backed similarity paths over a local artifact gallery, it has a sample-gallery builder plus CelebA-style local layout discovery, it exposes a minimal OpenAI-compatible chat-completions adapter for image similarity requests with both non-streaming and SSE streaming responses, and it includes a small built-in browser demo for one-frame webcam capture with optional face-box overlays. The full CelebA gallery workflow still blocks RC1.
The browser demo also includes explicit low-rate live polling, but that remains client-side polling rather than a server-side repeated-frame API.
This worktree has a measured local smoke/benchmark baseline, but it is not yet an authoritative pilot validation because Docker and the real model/gallery assets were unavailable here.

## Local Release Checks

Run the local smoke test against a running service:

```bash
python scripts/smoke_release.py --base-url http://localhost:8000 --api-key change-me-local-dev-key
python scripts/smoke_release.py --base-url http://localhost:8000 --api-key change-me-local-dev-key --check-diagnostics
```

Run the sequential local benchmark suite:

```bash
python scripts/benchmark_api.py --base-url http://localhost:8000 --api-key change-me-local-dev-key --endpoint all --requests 20
```

Run the strict release-candidate test pass:

```bash
python3.12 -m pytest -W error
```

Expected local behavior when assets are missing:
- `/readyz` may return `503` with `status: not_ready`.
- The smoke script should still pass if the service responds correctly to health, auth, native, chat, and demo checks.
- The benchmark script should still produce a useful report, with `engine_not_ready` counted as a valid not-ready outcome.
- Smoke tests must be run against the intended runtime target, not a guessed environment.
- Benchmark numbers must be measured and recorded, not invented.

Container packaging checks before a pilot release:
- build the CPU-only Docker image successfully;
- confirm the image runs as a non-root user on port 8000;
- confirm `reports/`, model artifacts, gallery artifacts, API keys, and `.env` are not baked into the image;
- run the smoke script against the container successfully;
- keep model and gallery mounts read-only for serving.
- Docker build verification must occur on a Docker-capable machine.

Production configuration checks before a pilot release:
- run the app with `APP_ENV=production` and a non-default API key;
- keep `STRICT_STARTUP_VALIDATION=true` for pilot deployments that require fail-fast asset checks;
- confirm `/v1/diagnostics/startup` returns sanitized diagnostics with no secrets or raw paths unless path disclosure is explicitly enabled;
- confirm `DEBUG_IMAGE_RETENTION` remains disabled;
- confirm `STARTUP_VALIDATE_ASSETS` is set to the intended operating mode.
- Review legal and dataset usage before any external or commercial use.

Before a pilot release, at minimum:
- the dependency policy must be reviewed and kept CPU-only;
- the test suite must pass without warnings;
- the Docker image must build successfully;
- the smoke script must pass against the release target;
- the release target must report ready if it is expected to serve similarity results;
- at least one benchmark report must be recorded and reviewed;
- no privacy or security rule in this repository may be violated;
- the release notes must not claim production biometric identification.
- The pilot checklist must be completed.

## RC1 Forbidden Claim
Production biometric identification or verified celebrity recognition.
