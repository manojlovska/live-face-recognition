# Current State

## Status
Work Order 5 model asset management and loader skeleton implementation is complete.

## Current implemented state:
- `/healthz` exists and is public.
- `/readyz` exists and reports model status honestly while gallery remains not loaded.
- One-key Bearer authentication exists.
- `/v1/models` exists and is protected.
- `/v1/face/similarity` exists as a protected JSON contract but returns engine_not_ready.
- `/v1/face/similarity` accepts authenticated JSON requests.
- The image field must currently be a base64 data URL.
- JPEG, PNG, and WebP are the intended supported image MIME types.
- Image input is decoded and validated in memory.
- Model asset paths are configurable.
- YuNet and SFace asset presence can be checked.
- Model loading skeleton exists but real inference is not implemented.
- Valid images still return engine_not_ready because inference is not implemented.
- No uploaded images or decoded images are stored by default.
- No OpenAI chat completions endpoint exists yet.

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
- `/v1/models` route contract
- `/v1/face/similarity` contract with stub engine
- Image input decoding and validation
- Model asset manager
- CPU-only model loading skeleton
- Pytest-based health/config smoke tests
- Ruff and packaging configuration

## Missing
- Face detection
- Embeddings
- Gallery loading
- OpenAI-compatible chat endpoint
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
- Work Order 3: `/v1/models` and native `/v1/face/similarity` contract with stub engine.
- Work Order 4: image decoding and validation for native JSON image requests.
- Work Order 5: model asset management and CPU-only YuNet/SFace loading skeleton.

## Next recommended work:
- Work Order 6: add real YuNet face detection using loaded detector, returning face boxes only, still without SFace embeddings or gallery search.

## Do Not Do Next
- Do not add browser UI before the API exists.
- Do not process the full CelebA dataset before the gallery-builder design is implemented.
- Do not add GPU dependencies.
- Do not claim production readiness.
