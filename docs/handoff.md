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
- Benchmarks
- Browser demo

## Known Risks
- Dataset licensing and image rights.
- Privacy/biometric-data obligations.
- CPU latency unknown until benchmarked.
- OpenAI compatibility must remain explicitly scoped.

## Next Recommended Work Order
Work Order 11: add non-streaming OpenAI-compatible `/v1/chat/completions` adapter for image similarity requests.

## Do Not Do Next
- Do not add model inference before scaffold/tests are stable.
- Do not add browser demo yet.
- Do not process full CelebA yet.
- Do not add GPU, database server, or user accounts.
