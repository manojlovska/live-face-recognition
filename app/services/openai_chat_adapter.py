from __future__ import annotations

import json
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from urllib.parse import urlparse

from pydantic import ValidationError

from app.config import Settings
from app.core.errors import ChatCompletionsError
from app.services.face_similarity import FaceSimilarityEngine, FaceSimilarityRequest
from app.services.image_input import decode_data_url_image

_DEFAULT_TOP_K = 5


@dataclass(slots=True)
class OpenAIChatSimilarityRequest:
    model: str
    image_data_url: str
    top_k: int
    stream: bool = False


def analyze_chat_completion_request(
    payload: object,
    *,
    settings: Settings,
    engine: FaceSimilarityEngine,
) -> dict[str, object]:
    request, native_result = analyze_chat_completion_native_result(
        payload,
        settings=settings,
        engine=engine,
    )
    return build_chat_completion_response(native_result, model=request.model)


def analyze_chat_completion_native_result(
    payload: object,
    *,
    settings: Settings,
    engine: FaceSimilarityEngine,
) -> tuple[OpenAIChatSimilarityRequest, dict[str, object]]:
    request = parse_chat_completion_request(payload, settings=settings)
    native_request = _build_native_request(request)
    decoded_image = decode_data_url_image(request.image_data_url, settings.max_image_bytes)
    native_result = engine.analyze(native_request, decoded_image)
    return request, native_result


def parse_chat_completion_request(
    payload: object,
    *,
    settings: Settings,
) -> OpenAIChatSimilarityRequest:
    if not isinstance(payload, dict):
        raise ChatCompletionsError(
            message="Request body must be a JSON object.",
            code="invalid_chat_message",
            status_code=400,
        )

    stream = payload.get("stream")
    if stream is not None and not isinstance(stream, bool):
        raise ChatCompletionsError(
            message="The stream field must be a boolean when provided.",
            code="invalid_chat_message",
            status_code=400,
        )

    model = payload.get("model")
    if not isinstance(model, str) or not model.strip():
        raise ChatCompletionsError(
            message="The model field is required.",
            code="invalid_chat_message",
            status_code=400,
        )
    if model != settings.model_id:
        raise ChatCompletionsError(
            message="The requested model is not available.",
            code="model_not_found",
            status_code=404,
        )

    top_k_value = payload.get("top_k", _DEFAULT_TOP_K)
    if (
        isinstance(top_k_value, bool)
        or not isinstance(top_k_value, int)
        or not 1 <= top_k_value <= 20
    ):
        raise ChatCompletionsError(
            message="top_k must be an integer between 1 and 20.",
            code="invalid_chat_message",
            status_code=422,
        )

    messages = payload.get("messages")
    if not isinstance(messages, list) or not messages:
        raise ChatCompletionsError(
            message="The messages field must contain a user image request.",
            code="image_required",
            status_code=400,
        )

    image_urls: list[str] = []
    user_image_found = False
    for message in messages:
        _validate_message_shape(message)
        role = message.get("role")
        content = message.get("content")

        if message.get("tool_calls") or message.get("function_call") or message.get("audio"):
            raise ChatCompletionsError(
                message="Tool, function, and audio messages are not supported.",
                code="invalid_chat_message",
                status_code=400,
            )
        if message.get("files"):
            raise ChatCompletionsError(
                message="File inputs are not supported.",
                code="invalid_chat_message",
                status_code=400,
            )

        if role == "user":
            user_image_found = True
            if not isinstance(content, list) or not content:
                raise ChatCompletionsError(
                    message="User message content must be a list of text and image_url parts.",
                    code="invalid_chat_message",
                    status_code=400,
                )
            image_urls.extend(_extract_user_image_urls(content))
            continue

        if role in {"system", "assistant"}:
            if _contains_image_part(content):
                raise ChatCompletionsError(
                    message="Only user image messages are supported.",
                    code="invalid_chat_message",
                    status_code=400,
                )
            continue

        raise ChatCompletionsError(
            message="Unsupported message role.",
            code="invalid_chat_message",
            status_code=400,
        )

    if not user_image_found:
        raise ChatCompletionsError(
            message="A user image is required.",
            code="image_required",
            status_code=400,
        )

    if not image_urls:
        raise ChatCompletionsError(
            message="A user image is required.",
            code="image_required",
            status_code=400,
        )
    if len(image_urls) > 1:
        raise ChatCompletionsError(
            message="Only one image is supported per request.",
            code="multiple_images_not_supported",
            status_code=400,
        )

    image_data_url = image_urls[0]
    if _is_remote_image_url(image_data_url):
        raise ChatCompletionsError(
            message="Remote image URLs are not supported.",
            code="remote_image_url_not_supported",
            status_code=400,
        )

    try:
        return OpenAIChatSimilarityRequest(
            model=model,
            image_data_url=image_data_url,
            top_k=top_k_value,
            stream=bool(stream),
        )
    except ValidationError as exc:
        raise ChatCompletionsError(
            message="The chat request is invalid.",
            code="invalid_chat_message",
            status_code=422,
        ) from exc


def build_chat_completion_response(
    native_result: dict[str, object],
    *,
    model: str,
) -> dict[str, object]:
    content_payload = build_chat_completion_content(native_result, model=model)

    return {
        "id": f"chatcmpl-local-{uuid.uuid4().hex}",
        "object": "chat.completion",
        "created": 0,
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": json.dumps(
                        content_payload,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
    }


def build_chat_completion_content(
    native_result: dict[str, object],
    *,
    model: str,
) -> dict[str, object]:
    content_payload = {
        "result_type": "face_similarity",
        "model": native_result.get("model", model),
        "mode": native_result.get("mode"),
        "faces": native_result.get("faces", []),
        "disclaimer": native_result.get(
            "disclaimer",
            "Similarity result only; not identity verification.",
        ),
    }
    if "gallery" in native_result:
        content_payload["gallery"] = native_result["gallery"]
    return content_payload


def iter_chat_completion_chunks(
    native_result: dict[str, object],
    *,
    model: str,
) -> Iterator[str]:
    stream_id = f"chatcmpl-local-{uuid.uuid4().hex}"
    try:
        yield _sse_event(
            _build_chat_completion_chunk(
                stream_id=stream_id,
                model=model,
                delta={"role": "assistant"},
                finish_reason=None,
            )
        )
        content_payload = build_chat_completion_content(native_result, model=model)
        yield _sse_event(
            _build_chat_completion_chunk(
                stream_id=stream_id,
                model=model,
                delta={
                    "content": json.dumps(
                        content_payload,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                },
                finish_reason=None,
            )
        )
        yield _sse_event(
            _build_chat_completion_chunk(
                stream_id=stream_id,
                model=model,
                delta={},
                finish_reason="stop",
            )
        )
    except Exception:
        yield _sse_event(
            _build_chat_completion_chunk(
                stream_id=stream_id,
                model=model,
                delta={
                    "content": json.dumps(
                        {
                            "error": {
                                "message": "Streaming response failed.",
                                "type": "server_error",
                                "code": "streaming_response_error",
                            }
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                },
                finish_reason="stop",
            )
        )
    finally:
        yield "data: [DONE]\n\n"


def _build_native_request(request: OpenAIChatSimilarityRequest) -> FaceSimilarityRequest:
    return FaceSimilarityRequest(
        image=request.image_data_url,
        top_k=request.top_k,
        return_face_boxes=True,
    )


def _build_chat_completion_chunk(
    *,
    stream_id: str,
    model: str,
    delta: dict[str, object],
    finish_reason: str | None,
) -> dict[str, object]:
    choice: dict[str, object] = {
        "index": 0,
        "delta": delta,
        "finish_reason": finish_reason,
    }
    return {
        "id": stream_id,
        "object": "chat.completion.chunk",
        "created": 0,
        "model": model,
        "choices": [choice],
    }


def _sse_event(payload: dict[str, object]) -> str:
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"data: {serialized}\n\n"


def _validate_message_shape(message: object) -> None:
    if not isinstance(message, dict):
        raise ChatCompletionsError(
            message="Messages must be JSON objects.",
            code="invalid_chat_message",
            status_code=400,
        )


def _extract_user_image_urls(content: list[object]) -> list[str]:
    image_urls: list[str] = []
    for part in content:
        if not isinstance(part, dict):
            raise ChatCompletionsError(
                message="Message content parts must be JSON objects.",
                code="invalid_chat_message",
                status_code=400,
            )
        part_type = part.get("type")
        if part_type == "text":
            continue
        if part_type == "image_url":
            image_url_part = part.get("image_url")
            if not isinstance(image_url_part, dict):
                raise ChatCompletionsError(
                    message="image_url parts must contain an image_url object.",
                    code="invalid_chat_message",
                    status_code=400,
                )
            url = image_url_part.get("url")
            if not isinstance(url, str) or not url.strip():
                raise ChatCompletionsError(
                    message="image_url.url must be a non-empty string.",
                    code="invalid_chat_message",
                    status_code=400,
                )
            image_urls.append(url.strip())
            continue
        raise ChatCompletionsError(
            message="Unsupported message content type.",
            code="invalid_chat_message",
            status_code=400,
        )
    return image_urls


def _contains_image_part(content: object) -> bool:
    if not isinstance(content, list):
        return False
    for part in content:
        if isinstance(part, dict) and part.get("type") == "image_url":
            return True
    return False


def _is_remote_image_url(url: str) -> bool:
    if url.startswith("data:"):
        return False
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"}
