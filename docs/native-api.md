# Native Face-Similarity API

## Endpoint

```http
POST /v1/face/similarity
Authorization: Bearer <FACE_API_KEY>
```

## Request Format

This work order supports JSON only. Multipart upload and remote image URLs are deferred.

The `image` field must be a base64 data URL:

```text
data:image/jpeg;base64,...
data:image/png;base64,...
data:image/webp;base64,...
```

Plain base64 strings are rejected for now.

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
- `image` must be a `data:image/...;base64,...` data URL.
- `top_k` defaults to `5`.
- `top_k` must be between `1` and `20`.
- `return_face_boxes` defaults to `true`.
- Supported MIME types are `image/jpeg`, `image/png`, and `image/webp`.
- `FACE_MAX_IMAGE_BYTES` limits decoded image size in bytes.

## Current Behavior

Authorized valid image requests are decoded and validated in memory. If the YuNet detector is loaded, the endpoint returns detection-only face boxes. If the detector is missing or unavailable, the request returns `503 Service Unavailable` with:

```json
{
  "error": {
    "message": "Face similarity engine is not ready. Models and gallery are not loaded.",
    "type": "service_unavailable",
    "code": "engine_not_ready"
  }
}
```

When detection-only mode is available, the response has this shape:

```json
{
  "object": "face_similarity.detection_result",
  "model": "celeba-face-similarity-cpu",
  "mode": "detection_only",
  "faces": [
    {
      "box": [112, 80, 220, 220],
      "detection_score": 0.97,
      "landmarks": {
        "right_eye": [150, 130],
        "left_eye": [190, 130],
        "nose_tip": [170, 155],
        "right_mouth_corner": [152, 185],
        "left_mouth_corner": [188, 185]
      },
      "top_matches": []
    }
  ],
  "disclaimer": "Detection-only result. Similarity matching is not implemented yet."
}
```

If no faces are detected, the response still returns HTTP `200` with:

```json
{
  "object": "face_similarity.detection_result",
  "model": "celeba-face-similarity-cpu",
  "mode": "detection_only",
  "faces": [],
  "disclaimer": "No faces detected. Similarity matching is not implemented yet."
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
- Malformed data URLs return `invalid_image_data_url`.
- Unsupported MIME types return `unsupported_image_type`.
- Invalid base64 returns `invalid_image_base64`.
- Decoded images over `FACE_MAX_IMAGE_BYTES` return `image_too_large`.
- Non-image bytes return `invalid_image`.
- Invalid `top_k` returns validation error.
- Valid authorized requests return detection-only results when YuNet is loaded.
- Valid authorized requests return `engine_not_ready` when YuNet is not loaded or cannot be used.
- Detection output never includes embeddings.
- `top_matches` is an empty list until gallery search exists.
- No face requests return HTTP `200` with an empty `faces` list.

## Privacy Behavior
Uploaded image data is decoded in memory and discarded by default. No uploaded images or decoded images are stored by default.
