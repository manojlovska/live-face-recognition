# Native Face-Similarity API

## Endpoint

```http
POST /v1/face/similarity
Authorization: Bearer <FACE_API_KEY>
```

## Supported Input Forms
MVP should support at least one of these:

1. JSON with base64 data URL
2. multipart image upload

The implementation must document which form is available first.

## Example JSON Request

```json
{
  "image": "data:image/jpeg;base64,...",
  "top_k": 5,
  "max_faces": 1
}
```

## Example Response

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
- Unsupported media type returns validation error.
- Oversized image returns request-too-large error.
- No face returns a structured no-face result or error, as specified in `docs/error-handling.md`.
- Multi-face behavior must be explicit: process best face by default or return multiple faces if requested.

## Privacy Behavior
Uploaded image data is processed in memory and discarded by default.
