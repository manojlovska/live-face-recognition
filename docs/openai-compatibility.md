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

`/v1/chat/completions` exists and supports both non-streaming and `stream=true` image similarity requests.

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
- `stream=true` for SSE response streaming

Unsupported behavior:
- remote image URLs
- multiple images per request
- plain base64 without a data URL prefix
- tool calls
- function calls
- audio
- files

## Local `top_k` Extension
`top_k` is a local extension, not standard OpenAI API behavior. If supplied, it is validated the same way as the native endpoint and defaults to `5`.

## Non-Streaming Response Content
The assistant message content is JSON text containing face-similarity results. It must include or preserve the disclaimer that the result is similarity-only and not identity verification.

## Streaming Response Content
When `stream=true`, the endpoint returns `text/event-stream` and emits OpenAI-style `chat.completion.chunk` frames.

Recommended streaming pattern:

```text
data: {"id":"chatcmpl-local-...","object":"chat.completion.chunk",...}

data: {"id":"chatcmpl-local-...","object":"chat.completion.chunk",...}

data: {"id":"chatcmpl-local-...","object":"chat.completion.chunk",...}

data: [DONE]
```

Recommended chunk sequence:
- first chunk sets `delta.role = "assistant"`
- content chunk streams the JSON face-similarity payload as a string
- final chunk sets `finish_reason = "stop"`
- final SSE frame is `data: [DONE]`

The streamed content is the same privacy-filtered face-similarity payload used by the non-streaming adapter. It is response streaming, not live video streaming, and token-level generation is not implemented.

## Limitations
- no tool calls
- no function calls
- no remote image URLs
- one image only
- no token-level model generation
- `stream=true` is response streaming only
- no live webcam streaming
- the built-in browser demo calls the native `/v1/face/similarity` endpoint instead of the OpenAI adapter
- the built-in browser demo can optionally draw boxes from the native endpoint response, but it still sends one request per click

## Compatibility Test Requirement
At least one test instantiates the OpenAI Python client and calls the local service through `base_url`.
