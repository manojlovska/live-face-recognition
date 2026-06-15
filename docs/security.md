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

## Logging Rules
Do not log:
- base64 image payloads;
- raw image bytes;
- face embeddings;
- raw embedding vectors;
- Authorization headers;
- API keys;
- full request bodies containing images.

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
