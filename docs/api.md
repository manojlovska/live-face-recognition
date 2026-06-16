# API Overview

## API Families
The service exposes:

1. Operational endpoints
2. Native face-similarity endpoints
3. OpenAI-compatible endpoints

## Operational Endpoints

### `GET /healthz`
Returns process liveness. Does not require model/gallery readiness.

### `GET /readyz`
Returns readiness state. Should report whether required models and gallery artifacts are loaded.

### `GET /v1/models`
Returns the configured model metadata and requires `Authorization: Bearer <FACE_API_KEY>`.

### `GET /v1/diagnostics/startup`
Returns sanitized startup diagnostics and requires `Authorization: Bearer <FACE_API_KEY>`.
This endpoint is operationally useful for startup checks, but it is protected because it reports configuration state.

### `GET /demo`
Returns the built-in browser demo HTML page. The demo page is public, but any API request it sends still requires Bearer auth.
The demo can show optional face-box overlays from a single captured frame, and it now also supports explicit low-rate live polling from the browser using the same native endpoint.
The polling mode is client-side, opt-in, and throttled.
The repository also includes local smoke-test and benchmark scripts that exercise these routes against a running service. They are tooling only and add no API routes.

## Native Endpoint

### `POST /v1/face/similarity`
Canonical endpoint for face-similarity inference.

Expected responsibilities:
- validate API key;
- accept a JSON data-URL image request;
- validate request shape;
- decode and validate the image in memory;
- return `engine_not_ready` until model loading exists;
- later: detect face(s), compute embeddings, search gallery, return top-k matches.

The browser demo uses this endpoint for both one-frame capture and explicit low-rate live polling. There is no separate repeated-frame or video-streaming endpoint.

## OpenAI-Compatible Endpoints

### `POST /v1/chat/completions`
Accepts a supported OpenAI-style image request and returns an assistant message containing structured face-similarity JSON, or OpenAI-style SSE chunks when `stream=true`.
The adapter reuses the native face-similarity pipeline.

## Versioning
API version is currently represented by `/v1` path prefix and model/gallery manifest versions.

## Unsupported in MVP
- General text generation
- Tool calling
- Function calling
- Audio input/output
- Fine-tuning
- User accounts
- Multi-key quota management
- Persistent conversation history
