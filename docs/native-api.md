# Native Face-Similarity API

## Endpoint

```http
POST /v1/face/similarity
Authorization: Bearer <FACE_API_KEY>
```

## Supported Input Forms
This work order adds the JSON contract only. Multipart upload and image decoding are deferred.

## Example JSON Request

```json
{
  "image": "data:image/jpeg;base64,...",
  "top_k": 5,
  "return_face_boxes": true
}
```

## Request Rules

- `image` is required and must be a string.
- `top_k` defaults to `5`.
- `top_k` must be between `1` and `20`.
- `return_face_boxes` defaults to `true`.

## Current Behavior

Authorized valid requests currently return `503 Service Unavailable` with:

```json
{
  "error": {
    "message": "Face similarity engine is not ready. Models and gallery are not loaded.",
    "type": "service_unavailable",
    "code": "engine_not_ready"
  }
}
```

## Future Success Response

When inference is implemented, the response should include the similarity result contract with detected faces, top matches, a model field, and the required disclaimer.

```json
{
  "object": "face_similarity.result",
  "model": "celeba-face-similarity-cpu",
  "faces": [
    {
      "box": [112, 80, 220, 220],
      "detection_score": 0.97,
      "top_matches": [
        {
          "rank": 1,
          "celeba_identity_id": "004321",
          "display_name": null,
          "similarity": 0.742
        }
      ]
    }
  ],
  "disclaimer": "Similarity result only; not identity verification."
}
```

## Required Behaviors
- Invalid/missing API key returns authentication error.
- Invalid request shape returns validation error.
- Invalid `top_k` returns validation error.
- Valid authorized requests currently return `engine_not_ready`.
- No face and multi-face behavior are deferred until image decoding and inference exist.

## Privacy Behavior
Uploaded image data is processed in memory and discarded by default.
