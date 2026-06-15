# Project Handoff

## Current Truth
- Scaffold commit exists: `5bb85a8` or current equivalent.
- Service has `/healthz` only.
- Tests and Ruff passed after scaffold.
- Documentation has been repaired to root-level `docs/`.

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
- Documentation starter pack and scaffold repair.

## Missing
- Auth layer
- `/readyz`
- `/v1/models`
- Native face-similarity endpoint
- Inference pipeline
- Model loader
- Gallery builder
- Benchmarks
- Browser demo

## Known Risks
- Dataset licensing and image rights.
- Privacy/biometric-data obligations.
- CPU latency unknown until benchmarked.
- OpenAI compatibility must remain explicitly scoped.

## Next Recommended Work Order
Work Order 2: one-key Bearer authentication and `/readyz`.

## Do Not Do Next
- Do not add model inference before scaffold/tests are stable.
- Do not add browser demo yet.
- Do not process full CelebA yet.
- Do not add GPU, database server, or user accounts.
