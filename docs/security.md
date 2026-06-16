# Security

## Security Goal
Keep the first release simple but safe: one API key, no production secrets in source, no face image retention by default, and predictable request limits.

## Authentication
Protected endpoints require:

```http
Authorization: Bearer <FACE_API_KEY>
```

The key is loaded from environment variable `FACE_API_KEY` or a documented equivalent.

- `FACE_API_KEY` is the single API key.
- Protected endpoints must require `Authorization: Bearer <key>`.
- `/healthz` and `/readyz` are public operational endpoints unless later changed.
- Keys must never be logged.
- Missing `FACE_API_KEY` fails closed for protected endpoints.

## Required Auth Behavior
- Missing Authorization header is rejected.
- Wrong scheme is rejected.
- Wrong token is rejected.
- Correct token is accepted.
- Logs must not include the token.

## Secrets Rules
- Never commit `.env` with real secrets.
- Never commit real API keys.
- Never print full Authorization headers.
- Use placeholders in docs and tests.
- If a secret is accidentally exposed, stop and report.

## Image Safety
- Reject unsupported image formats.
- Reject oversized images.
- Decode images defensively.
- Do not trust client-provided MIME type alone.
- Do not write uploaded images to disk by default.
- Enforce request size limits with `FACE_MAX_IMAGE_BYTES`.
- Model assets are operator-supplied local files; the service does not download them at runtime.
- Model asset presence and checksum checks must not expose raw file contents.
- Gallery embeddings and metadata are operator-supplied local files; the service does not download them at runtime.
- Do not log query embeddings or gallery embeddings.
- Similarity matches must come from loaded gallery metadata only.
- The offline gallery builder must not log raw image bytes or embeddings.
- The offline gallery builder must not write aligned face crops or debug images.
- The offline gallery builder may log safe dataset metadata, but it must not log raw source image bytes or derived embeddings.
- The OpenAI-compatible chat adapter must enforce the same auth, image-size, and image-format rules as the native endpoint.
- The OpenAI-compatible chat adapter must reject remote image URLs and multiple images.
- `stream=true` is supported as SSE response streaming only; it is not live video streaming.
- The browser demo must not persist API keys or captured images in browser storage.
- The browser demo's live polling mode must remain same-origin, opt-in, client-side, and throttled.
- The browser demo's live polling mode must stop when the camera stops or when the tab becomes hidden.
- The browser demo must not load third-party scripts or send data to third-party origins.
- The browser demo overlay must be drawn locally from the API response and must not perform browser-side recognition.
- The smoke-test and benchmark scripts must only contact the configured local/base URL and must not log or store API keys or image payloads.
- The smoke-test and benchmark scripts must not add telemetry, third-party analytics, or external reporting services.

## Logging Rules
Do not log:
- base64 image payloads;
- raw image bytes;
- face embeddings;
- raw embedding vectors;
- gallery embedding vectors;
- Authorization headers;
- API keys;
- full request bodies containing images.
- raw image bytes from gallery-building inputs.

Log only safe metadata such as:
- request ID;
- endpoint;
- success/failure;
- latency;
- image dimensions after validation;
- number of faces detected;
- error category.
- image payloads or decoded bytes.
- model asset paths or checksums unless the value is already a documented non-secret artifact.
- gallery artifact paths or checksums unless the value is already a documented non-secret artifact.
- builder input or output paths unless already documented as local non-secret artifacts.
- OpenAI message contents that include raw image payloads or decoded bytes.
- SSE chunk payloads that include raw image payloads or decoded bytes.

## Request Limits
The service should define:
- maximum request body size;
- maximum decoded image dimensions;
- maximum faces processed per request;
- maximum `top_k`;
- timeout behavior.

Exact values must be documented once implemented.

## Dependency Security
Before RC1, run a dependency audit such as `pip-audit` or document why it was not run.

## Threats Deferred to `threat-model.md`
The detailed threat model lives in `docs/threat-model.md`.
