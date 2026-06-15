# Current State

## Status
Work Order 1 scaffold implementation is complete and the repository layout has been repaired to root-level `docs/`.

## Current implemented state:
- CPU-only FastAPI scaffold exists.
- `/healthz` exists.
- `/readyz` exists and returns not_ready until models/gallery are implemented.
- Reusable one-key Bearer authentication dependency exists.
- Pytest and Ruff are configured.
- No protected inference endpoints exist yet.
- No `/v1/models` endpoint exists yet.
- No image ingestion or inference exists yet.
- No OpenAI-compatible chat endpoint exists yet.

## Current Truth
- Project goal is defined.
- CPU-only constraint is accepted.
- OpenAI-compatible API requirement is accepted.
- One-key auth requirement is accepted.
- YuNet + SFace is the proposed initial model stack.
- CelebA is the proposed gallery base, with licensing caution.
- No image or embedding retention by default is accepted.

## Implemented
- Python package scaffold
- FastAPI application entry point
- Basic settings loader
- `/healthz` route
- `/readyz` route
- API key authentication dependency
- Pytest-based health/config smoke tests
- Ruff and packaging configuration

## Missing
- Auth dependency
- Readiness endpoint
- OpenAI-compatible endpoints
- Native face-similarity endpoint
- Model downloader/loader
- Gallery artifacts and builder
- Full test coverage
- Benchmarks
- Browser demo

## Known Risks
- CelebA licensing may limit use to non-commercial research/demo contexts.
- Face data is sensitive and may trigger biometric-data obligations depending on deployment context.
- CPU performance must be measured, not assumed.
- OpenAI compatibility must be explicitly scoped; this is not a general LLM API.

## Last completed work:
- Work Order 1: initial FastAPI scaffold.
- Work Order 2: one-key Bearer authentication and `/readyz`.

## Next recommended work:
- Work Order 3: add `/v1/models` and native `/v1/face/similarity` contract with a stub engine.

## Do Not Do Next
- Do not add browser UI before the API exists.
- Do not process the full CelebA dataset before the gallery-builder design is implemented.
- Do not add GPU dependencies.
- Do not claim production readiness.
