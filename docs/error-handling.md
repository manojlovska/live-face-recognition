# Error Handling

## Goal
Errors should be clear, structured, and safe. They must not leak internal stack traces, secrets, raw payloads, or file paths containing sensitive information.

## Native Error Shape
Recommended native error:

```json
{
  "error": {
    "type": "invalid_request_error",
    "code": "invalid_image",
    "message": "The provided image could not be decoded.",
    "param": "image"
  }
}
```

## OpenAI-Compatible Error Shape
OpenAI-compatible endpoints should return an OpenAI-style error object where practical:

```json
{
  "error": {
    "message": "The provided image could not be decoded.",
    "type": "invalid_request_error",
    "param": "image",
    "code": "invalid_image"
  }
}
```

## Required Error Cases

| Case | Code suggestion | HTTP status |
|---|---|---:|
| Missing or invalid API key | `invalid_api_key` | 401 |
| Engine not ready | `engine_not_ready` | 503 |
| Malformed data URL | `invalid_image_data_url` | 400 |
| Unsupported image type | `unsupported_image_type` | 415 |
| Invalid base64 | `invalid_image_base64` | 400 |
| Decoded image too large | `image_too_large` | 413 |
| Invalid image bytes | `invalid_image` | 400 |
| Unsupported OpenAI model | `model_not_found` | 404 |
| Streaming not implemented | `streaming_not_implemented` | 400 |
| Missing image in chat request | `image_required` | 400 |
| Multiple images in chat request | `multiple_images_not_supported` | 400 |
| Remote image URL in chat request | `remote_image_url_not_supported` | 400 |
| Malformed chat message | `invalid_chat_message` | 400 or 422 |
| Unsupported route | `not_found` | 404 |
| Request too large | `request_too_large` | 413 |
| No face found | `no_face_detected` | 200 with empty faces |
| Too many faces | `too_many_faces` | 422 or process first face, to be decided |
| Model not ready | `model_not_ready` | 503 |
| Gallery not ready | `gallery_not_ready` | 503 |
| Gallery missing or not loaded | `gallery_not_loaded` | 503 |
| Gallery/query embedding dimension mismatch | `embedding_dimension_mismatch` | 500 |
| Embedding generation failed | `embedding_failed` | 200 with per-face embedding error marker |
| Unsupported OpenAI feature | `unsupported_feature` | 400 |

## Open Decisions
- Whether multi-face requests process all faces, the best face, or require explicit `max_faces`.

These decisions must be finalized before MVP.

## Authentication Error Shape
Authentication failures should use a compact, OpenAI-style error envelope:

```json
{
  "error": {
    "message": "Invalid or missing API key.",
    "type": "authentication_error",
    "code": "invalid_api_key"
  }
}
```

Return HTTP `401 Unauthorized` with `WWW-Authenticate: Bearer`.

## Engine Not Ready Shape
When YuNet is unavailable or not loaded, protected similarity requests should return:

```json
{
  "error": {
    "message": "Face similarity engine is not ready. Models and gallery are not loaded.",
    "type": "service_unavailable",
    "code": "engine_not_ready"
  }
}
```

Return HTTP `503 Service Unavailable`.

The OpenAI chat completions adapter uses the same error envelope and codes for its supported failure cases.

## Readiness Model Status
`/readyz` reports model status with the summary values `models_missing`, `present_not_loaded`, `detector_loaded_gallery_missing`, `embedding_models_loaded_gallery_missing`, `gallery_error`, `detector_error`, `embedder_error`, `loaded`, or `ready`.
This is operational status only and does not imply a successful similarity response when gallery artifacts are missing or corrupt.

## Detection Output
- Detection-only results are success responses, not errors.
- When YuNet is loaded, valid requests return HTTP `200` with `faces` and `top_matches: []`.
- When YuNet and SFace are loaded, valid requests return HTTP `200` with internal embedding metadata and `top_matches: []`.
- When YuNet, SFace, and a gallery artifact are loaded, valid requests return HTTP `200` with similarity matches in `top_matches`.
- When no faces are detected, the service still returns HTTP `200` with an empty `faces` list.
- Missing detector availability still uses `engine_not_ready`; no new error code is introduced in this work order.
- Per-face embedding failures return a success response with `embedding.generated: false` and `embedding.error: "embedding_failed"`.
- Gallery dimension mismatch returns HTTP `500` with `invalid_gallery_state` and `embedding_dimension_mismatch`.

## Chat Completions Error Shape
The OpenAI-compatible `/v1/chat/completions` adapter uses the same JSON envelope for supported failures:

```json
{
  "error": {
    "message": "The requested model is not available.",
    "type": "invalid_request_error",
    "code": "model_not_found"
  }
}
```

Required chat-completions error codes:
- `model_not_found` for unsupported models;
- `streaming_not_implemented` for `stream: true`;
- `image_required` when no usable user image is present;
- `multiple_images_not_supported` for more than one image;
- `remote_image_url_not_supported` for remote URLs;
- `invalid_chat_message` for malformed message shapes.

Native image-validation errors are passed through unchanged so the adapter and native endpoint stay aligned.
