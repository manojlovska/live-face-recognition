# Current State

## Status
Work Order 7 SFace embedding-generation implementation is complete.

## Current implemented state:
- `/healthz` exists and is public.
- `/readyz` exists and reports model status honestly while gallery remains not loaded.
- One-key Bearer authentication exists.
- `/v1/models` exists and is protected.
- `/v1/face/similarity` exists as a protected JSON contract that can return detection-only face boxes or internal embeddings when the models are loaded.
- `/v1/face/similarity` accepts authenticated JSON requests.
- The image field must currently be a base64 data URL.
- JPEG, PNG, and WebP are the intended supported image MIME types.
- Image input is decoded and validated in memory.
- Model asset paths are configurable.
- YuNet and SFace asset presence can be checked.
- Model loading skeleton exists and YuNet detection plus internal SFace embedding generation exist.
- If YuNet is available and loaded, valid images can return detection-only face boxes.
- If YuNet and SFace are available and loaded, the service can generate internal face embeddings.
- Raw embeddings are not returned by the public API.
- Detection-only mode does not return embeddings or CelebA matches.
- top_matches remains empty because CelebA gallery search is not implemented.
- `/readyz` remains not_ready because full similarity requires gallery loading and search.
- SFace similarity search and gallery loading are not implemented yet.
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
- Work Order 6: YuNet face detection returning face boxes only.
- Work Order 7: SFace face alignment and embedding generation for detected faces.

## Next recommended work:
- Work Order 8: add local gallery artifact loading and exact cosine similarity search over a small test gallery, still without full CelebA build.

## Do Not Do Next
- Do not add browser UI before the API exists.
- Do not process the full CelebA dataset before the gallery-builder design is implemented.
- Do not add GPU dependencies.
- Do not claim production readiness.
