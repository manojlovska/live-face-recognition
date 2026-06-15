# OpenAI Compatibility

## Purpose
The project offers a minimal OpenAI-compatible surface so users can reuse OpenAI SDK patterns with a custom `base_url`.

This service is not a general LLM. Compatibility is limited to the documented image-similarity path.

## Required Endpoints

### `GET /v1/models`
Returns an OpenAI-style model list containing `celeba-face-similarity-cpu`.

### `POST /v1/chat/completions`
Returns face-similarity results in the assistant message for supported image requests.

## Current State

`/v1/models` exists and is protected by Bearer API key auth.

`/v1/chat/completions` exists and supports non-streaming image similarity requests.

`stream=true` is not implemented yet.

## Supported Request Shape

```python
from openai import OpenAI

client = OpenAI(
    api_key="local-dev-key",
    base_url="http://localhost:8000/v1",
)

response = client.chat.completions.create(
    model="celeba-face-similarity-cpu",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Who is this face most similar to?"},
                {
                    "type": "image_url",
                    "image_url": {"url": "data:image/jpeg;base64,..."},
                },
            ],
        }
    ],
)
```

Supported behavior:
- `model`
- `messages`
- a user message with `content` as a list
- one `image_url` part whose `url` is a data URL
- optional text parts, which are ignored for now
- optional local extension `top_k`
- `stream` omitted or `false`

Unsupported behavior:
- remote image URLs
- multiple images per request
- plain base64 without a data URL prefix
- tool calls
- function calls
- audio
- files
- `stream=true` until Work Order 12

## Local `top_k` Extension
`top_k` is a local extension, not standard OpenAI API behavior. If supplied, it is validated the same way as the native endpoint and defaults to `5`.

## Response Content
The assistant message content is JSON text containing face-similarity results. It must include or preserve the disclaimer that the result is similarity-only and not identity verification.

## Compatibility Test Requirement
At least one test instantiates the OpenAI Python client and calls the local service through `base_url`.
