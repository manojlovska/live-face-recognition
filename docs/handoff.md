# Project Handoff

## Current Truth
- Scaffold commit exists: `5bb85a8` or current equivalent.
- Service has `/healthz`, `/readyz`, `/v1/models`, and `/v1/face/similarity` contract routes.
- Valid `/v1/face/similarity` image requests are decoded and validated in memory.
- Model asset paths are configurable and model presence can be checked.
- YuNet detection-only responses, internal SFace embeddings, and gallery-backed similarity results can be returned when the runtime pieces are loaded.
- Raw embeddings are not returned by default.
- Tests and Ruff passed after scaffold and repair work.
- Documentation lives at root-level `docs/`.
- Local gallery artifacts can be loaded from `data/gallery/` or test fixtures.
- A small CelebA-like gallery builder skeleton can process local sample directories.
- The builder now understands common CelebA-style layouts and partition files.
- The builder records quality and performance reporting for local runs.
- The OpenAI chat adapter now supports both non-streaming responses and `stream=true` SSE chunks.
- A small built-in browser demo now captures one webcam frame on demand and sends it to the native API.
- The browser demo can optionally draw face boxes from the single-frame response.
- The browser demo now also supports explicit low-rate live polling with client-side throttling and the existing native API.
- Local smoke-test tooling and sequential local benchmark tooling are now available.

## Current State After Work Order 20
- Release-candidate documentation has been consolidated into a pilot checklist, operator runbook, and RC1 draft notes.
- Benchmark results remain a template until a real measured run is recorded.
- The project remains a CPU-only similarity service and does not claim identity verification or commercial readiness.

## Current State After Work Order 21
- Warning-free tests passed and a local smoke/benchmark baseline was measured directly from the repository root.
- The smoke and benchmark scripts now run without extra `PYTHONPATH` setup.
- Docker validation and real model/gallery RC validation remain blocked in this environment.
- Benchmark results are recorded, but they reflect the not-ready local runtime rather than a full pilot target.

## Current State After Work Order 24R
- Ready-path RC validation was completed on a Docker-capable machine with mounted YuNet/SFace models and a small local gallery.
- Smoke checks passed for both no-assets and mounted-assets container runs.
- Ready-path benchmark results were recorded for native, chat, and chat-stream paths using a representative local face image.
- The remaining release blocker is human legal/dataset approval, not runtime readiness.

## Current State After Work Order 25
- RC1 release-package documentation has been prepared for human review.
- The project remains a controlled-pilot candidate, not a final commercial release.
- Human legal/dataset approval is still pending before any broader or external use.

## Current State After Work Order 27
- A GitHub Release draft for `v0.1.0-rc1` is prepared in docs but has not been published.
- The internal RC1 announcement draft is prepared for maintainers and operators.
- RC1 remains a controlled-pilot release candidate, not a final release.

## Current State After Work Order 31
- The v0.1.0-rc1 GitHub Release has been published.
- Post-publication verification documentation exists.
- Pilot-operator onboarding documentation exists.
- RC1 remains a release candidate, not a final release.
- The approved use scope is documented in the human approval notes.

## Product Goal
CPU-only, OpenAI-compatible CelebA face-similarity API with one-key auth, no image retention by default, and later browser webcam demo.

## Accepted Strategic Decisions
- CPU-only for MVP/RC1.
- OpenAI-compatible API via `/v1/models` and `/v1/chat/completions`.
- Native `/v1/face/similarity` remains canonical vision endpoint.
- YuNet + SFace initial model stack.
- CelebA-derived gallery, with licensing caution.
- No user image or embedding retention by default.
- Similarity-only language, not identity verification.

## Implemented
- Documentation starter pack, scaffold repair, readiness/auth layer, protected contract routes, image validation, model asset loading skeleton, YuNet detection-only output, internal SFace embeddings, local gallery search over artifact fixtures, and an offline sample-gallery builder skeleton.

## Missing
- Full CelebA gallery build
- Benchmark results

## Known Risks
- Dataset licensing and image rights.
- Privacy/biometric-data obligations.
- CPU latency unknown until benchmarked.
- OpenAI compatibility must remain explicitly scoped.

## Next Recommended Work Order
Work Order 32: run a pilot-operator dry run using the onboarding guide and capture feedback.

## Do Not Do Next
- Do not add model inference before scaffold/tests are stable.
- Do not process full CelebA yet.
- Do not add GPU, database server, or user accounts.
