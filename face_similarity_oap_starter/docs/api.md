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

## Native Endpoint

### `POST /v1/face/similarity`
Canonical endpoint for face-similarity inference.

Expected responsibilities:
- validate API key;
- accept an image;
- validate image size/type;
- detect face(s);
- compute embeddings;
- search gallery;
- return top-k matches.

## OpenAI-Compatible Endpoints

### `GET /v1/models`
Returns available model metadata. MVP model name:

```text
celeba-face-similarity-cpu
```

### `POST /v1/chat/completions`
Accepts a supported OpenAI-style image request and returns an assistant message containing structured face-similarity JSON.

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
