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
| Unsupported route | `not_found` | 404 |
| Unsupported model | `model_not_found` | 404 |
| Invalid image | `invalid_image` | 400 |
| Unsupported image type | `unsupported_image_type` | 415 |
| Request too large | `request_too_large` | 413 |
| No face found | `no_face_detected` | 422 or 200 with empty faces, to be decided |
| Too many faces | `too_many_faces` | 422 or process first face, to be decided |
| Model not ready | `model_not_ready` | 503 |
| Gallery not ready | `gallery_not_ready` | 503 |
| Unsupported OpenAI feature | `unsupported_feature` | 400 |

## Open Decisions
- Whether no-face should be an error or a successful response with `faces: []`.
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
Until model loading exists, protected similarity requests should return:

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
