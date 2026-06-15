# Project Handoff

## Current Truth
Initial OAP documentation pack has been created. No implementation exists yet unless a later commit adds it.

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
- Documentation starter pack only.

## Missing
- Code scaffold
- Tests
- API implementation
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
Create project scaffold:
- `pyproject.toml`
- app package
- FastAPI `app.main:app`
- settings model
- `/healthz`
- minimal tests
- ruff configuration
- README quickstart

## Do Not Do Next
- Do not add model inference before scaffold/tests are stable.
- Do not add browser demo yet.
- Do not process full CelebA yet.
- Do not add GPU, database server, or user accounts.

## Last Updated
Initial generated state.
