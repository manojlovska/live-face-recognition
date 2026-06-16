# Current State

## Status
Work Order 19 release-candidate cleanup for test warnings and dependency bounds is complete.

## Current implemented state:
- Startup configuration validation exists.
- The app distinguishes development, test, and production configuration modes.
- Strict startup validation can fail fast on unsafe settings.
- A protected `/v1/diagnostics/startup` endpoint exposes sanitized startup diagnostics.
- Diagnostics do not expose API keys, image payloads, or embeddings.
- A minimal CPU-only Dockerfile exists.
- Container runs the FastAPI service with Uvicorn on port 8000.
- Model files, gallery artifacts, reports, API keys, and .env files are not baked into the image.
- Model and gallery artifacts are expected to be mounted at runtime.
- Cloud deployment manifests are not implemented yet.
- Local smoke-test tooling exists for API and browser-demo contract checks.
- Local benchmark tooling exists for native, chat, and streaming chat endpoints.
- Benchmarking is sequential and local by default.
- The tools do not store API keys or image payloads in reports.
- The test suite is expected to pass without the previous Starlette/FastAPI/TestClient deprecation warning.
- Runtime and test dependency bounds have been reviewed for CPU-only release-candidate use.
- No GPU, database, Redis, Celery, or frontend build dependencies are included.
- Production monitoring and load testing are not implemented yet.
- The browser demo at /demo supports one-frame capture.
- The browser demo can optionally draw face boxes from the API response.
- The browser demo now includes explicit low-rate live polling using the existing /v1/face/similarity endpoint.
- Live polling is client-side, opt-in, and throttled.
- The project still does not implement server-side video streaming, WebSockets, or a repeated-frame API.
- `/healthz` exists and is public.
- `/readyz` exists and reports model and gallery status honestly.
- One-key Bearer authentication exists.
- `/v1/models` exists and is protected.
- `/v1/face/similarity` exists as a protected JSON contract that can return detection-only face boxes, internal embeddings, or gallery-backed similarity results.
- `/v1/chat/completions` supports both non-streaming and `stream=true` OpenAI-compatible image similarity requests.
- A small built-in browser demo is available at `/demo`.
- `/v1/face/similarity` accepts authenticated JSON requests.
- The OpenAI chat endpoint accepts one data URL image in an OpenAI-style `image_url` content part.
- The OpenAI chat endpoint returns assistant content as JSON text in non-streaming mode and OpenAI-style SSE chunk frames in streaming mode.
- The image field must currently be a base64 data URL.
- JPEG, PNG, and WebP are the intended supported image MIME types.
- Image input is decoded and validated in memory.
- Model asset paths are configurable.
- YuNet and SFace asset presence can be checked.
- Model loading skeleton exists and YuNet detection plus internal SFace embedding generation exist.
- A local gallery artifact can be loaded.
- Exact cosine similarity search over a loaded gallery exists.
- An offline gallery builder skeleton can process a small CelebA-like sample directory.
- The gallery builder can discover common local CelebA-style layouts.
- Optional partition-file parsing exists.
- The builder reads a CelebA-style identity file and writes gallery embeddings, metadata, manifest, and build report.
- The builder writes quality and performance reporting into `gallery_build_report.json`.
- If YuNet is available and loaded, valid images can return detection-only face boxes.
- If YuNet and SFace are available and loaded, the service can generate internal face embeddings.
- If YuNet, SFace, and a gallery artifact are loaded, the service can return `top_matches` from the gallery.
- Raw embeddings are not returned by the public API.
- Detection-only mode does not return embeddings or CelebA matches.
- top_matches is empty when no gallery artifact is loaded and populated when one is available.
- `/readyz` returns ready only when the detector, embedder, and gallery are loaded; otherwise it remains not_ready.
- Gallery support is artifact-based and test-gallery oriented.
- The builder is sample-scale first; full CelebA processing is not implemented yet.
- No uploaded images or decoded images are stored by default.
- `stream=true` uses OpenAI-style SSE chunk frames.
- The browser demo can capture one webcam frame and can also run explicit low-rate live polling against `/v1/face/similarity`.
- The browser demo can optionally draw face boxes from captured-frame API responses.
- The browser demo keeps live polling client-side, opt-in, and single-flight.
- Local smoke-test tooling and sequential local benchmark tooling are now implemented.
- WebSockets are not implemented.
- The project still does not download CelebA.

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
- Gallery artifact loader and cosine search
- Offline gallery builder skeleton
- Pytest-based health/config smoke tests
- Ruff and packaging configuration
- Browser demo at `/demo` with one-frame capture, optional face-box overlay, and low-rate live polling

## Missing
- Full CelebA gallery build
- OpenAI-compatible chat endpoint
- Model downloader
- Gallery artifacts and builder
- Full test coverage
- Benchmark results

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
- Work Order 8: local gallery artifact loading and exact cosine similarity search.
- Work Order 9: offline gallery builder skeleton for a CelebA-like sample directory.
- Work Order 10: CelebA layout discovery, partition parsing, and builder quality/performance reporting.
- Work Order 11: non-streaming OpenAI-compatible `/v1/chat/completions` adapter for image similarity requests.
- Work Order 12: OpenAI-compatible `stream=true` SSE chat completions.
- Work Order 13: small built-in browser demo for one-frame webcam capture.
- Work Order 14: optional client-side face-box overlay for the browser demo.
- Work Order 15: explicit low-rate live polling for the browser demo using the existing native API.
- Work Order 16: local benchmark and release smoke-test tooling.
- Work Order 17: CPU-only Docker packaging and production run documentation.
- Work Order 18: production configuration validation and startup diagnostics.
- Work Order 19: release-candidate cleanup for test warnings and dependency bounds.

## Next recommended work:
- Work Order 19: add release-candidate cleanup by resolving the Starlette/TestClient deprecation warning and tightening test/runtime dependency versions.

## Do Not Do Next
- Do not add browser UI before the API exists.
- Do not add GPU dependencies.
- Do not claim production readiness.
