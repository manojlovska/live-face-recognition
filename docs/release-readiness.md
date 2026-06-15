# Release Readiness

## Release Principle
Feature completion is not release readiness. Release readiness requires evidence: tests, docs, benchmark results, privacy/security review, and honest limitations.

## MVP Gates

| Gate | Required evidence | Status |
|---|---|---|
| Install | documented local install works | not started |
| Auth | one-key auth tested | in progress |
| Health | `/healthz` tested | in progress |
| Readiness | `/readyz` tested | in progress |
| Models | `/v1/models` tested | in progress |
| Native API | `/v1/face/similarity` tested | in progress |
| OpenAI API | non-streaming `/v1/chat/completions` works | not started |
| CPU inference | YuNet detection and internal SFace embeddings work without GPU | in progress |
| Gallery | small gallery works | complete |
| Privacy | no image/embedding retention by default | not started |
| Docs | README and core docs updated | in progress |
| Tests | `pytest` and `ruff check` pass | in progress |

## RC1 Gates

| Gate | Required evidence | Status |
|---|---|---|
| Full gallery | reproducible CelebA gallery workflow | not started |
| Streaming | OpenAI-style `stream=true` works | not started |
| Live frames | repeated-frame API tested | not started |
| Browser demo | HTML5 webcam demo works | not started |
| Benchmarks | CPU benchmark results documented | not started |
| Security | auth, request limits, no-secret checks | not started |
| Privacy | no-retention policy documented and tested where practical | not started |
| Model card | complete and honest | initial draft |
| Dataset licensing | limitations documented | initial draft |
| Error handling | structured errors documented/tested | in progress |
| Compatibility | OpenAI Python client compatibility test | not started |
| Release language | no overclaims | in progress |

## RC1 Allowed Claim
Controlled-pilot-ready CPU-only research service for CelebA-based face similarity.

The API now supports detector-only, embedding-only, and gallery-backed similarity paths over a local artifact gallery, and it also has a sample-gallery builder. The full CelebA gallery workflow still blocks RC1.

## RC1 Forbidden Claim
Production biometric identification or verified celebrity recognition.
