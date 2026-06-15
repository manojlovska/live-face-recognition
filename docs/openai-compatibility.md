# OpenAI Compatibility

## Purpose
The project offers OpenAI-compatible endpoints so users can reuse OpenAI SDK patterns with a custom `base_url`.

This service is not a general LLM. Compatibility is limited to the documented vision request path.

## Required MVP Endpoints

### `GET /v1/models`
Must return an OpenAI-style model list containing:

```text
celeba-face-similarity-cpu
```

### `POST /v1/chat/completions`
Must accept supported image-containing chat requests and return face-similarity results in the assistant message.

## Current State

`/v1/models` now exists and is protected by Bearer API key auth.

`/v1/chat/completions` is still not implemented.

## Example Client Use

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

## Supported in MVP
- OpenAI Python client with custom `base_url`
- Bearer API key
- `/v1/models`
- `/v1/chat/completions` later
- image input using base64 data URL
- non-streaming response

## Target by RC1
- `stream=true` response streaming using SSE
- OpenAI-style error objects
- compatibility tests using the OpenAI Python package

## Not Supported
- General text generation
- Model reasoning
- Tool calls
- Function calls
- Audio
- Files API
- Assistants API
- Fine-tuning
- Embeddings API
- Persistent conversations

## Response Content
The assistant message should contain structured JSON text with face-similarity results. It must include or preserve a disclaimer that the result is similarity-only and not identity verification.

## Compatibility Test Requirement
At least one test or example must instantiate the OpenAI Python client and call the local service through `base_url`.
