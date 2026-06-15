from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from tests.image_helpers import make_image_data_url
from tests.test_openai_chat_adapter import (
    ChatRuntime,
    FakeSFaceEmbedder,
    FakeYuNetDetector,
    _auth_headers,
    _build_app,
    _build_gallery_store,
    _chat_request,
    _face_row,
)


def _build_streaming_app(
    detector: object | None, embedder: object | None, gallery_store: object | None
) -> TestClient:
    return TestClient(
        _build_app(
            ChatRuntime(
                detector=detector,
                embedder=embedder,
                gallery_store=gallery_store,
            )
        )
    )


def _extract_sse_events(body: str) -> list[str]:
    events: list[str] = []
    lines: list[str] = []
    for line in body.splitlines():
        if line.startswith("data: "):
            lines.append(line.removeprefix("data: ").strip())
            continue
        if line == "":
            if lines:
                events.append("\n".join(lines))
                lines = []
    if lines:
        events.append("\n".join(lines))
    return events


def _streaming_client() -> TestClient:
    return _build_streaming_app(
        detector=FakeYuNetDetector(_face_row()),
        embedder=FakeSFaceEmbedder(),
        gallery_store=_build_gallery_store(),
    )


def test_chat_completion_streaming_happy_path_returns_sse_chunks(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    client = _streaming_client()

    with client.stream(
        "POST",
        "/v1/chat/completions",
        headers=_auth_headers(),
        json=_chat_request(make_image_data_url("JPEG"), stream=True, top_k=2),
    ) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        body = "".join(response.iter_text())

    events = _extract_sse_events(body)
    assert events[-1] == "[DONE]"

    chunk_objects = [json.loads(event) for event in events[:-1]]
    assert chunk_objects[0]["object"] == "chat.completion.chunk"
    assert chunk_objects[0]["choices"][0]["delta"]["role"] == "assistant"

    content_chunk = chunk_objects[1]["choices"][0]["delta"]["content"]
    content_payload = json.loads(content_chunk)
    assert content_payload["result_type"] == "face_similarity"
    assert content_payload["mode"] == "similarity"
    assert "data:image" not in content_chunk
    assert "vector" not in content_chunk

    assert chunk_objects[2]["choices"][0]["finish_reason"] == "stop"


def test_chat_completion_streaming_matches_non_streaming_content(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    client = _streaming_client()
    request = _chat_request(make_image_data_url("PNG"), stream=False, top_k=5)

    response = client.post("/v1/chat/completions", headers=_auth_headers(), json=request)
    assert response.status_code == 200
    non_stream_content = json.loads(response.json()["choices"][0]["message"]["content"])

    with client.stream(
        "POST",
        "/v1/chat/completions",
        headers=_auth_headers(),
        json=_chat_request(make_image_data_url("PNG"), stream=True, top_k=5),
    ) as stream_response:
        stream_body = "".join(stream_response.iter_text())

    stream_events = _extract_sse_events(stream_body)
    stream_chunks = [json.loads(event) for event in stream_events[:-1]]
    stream_content = json.loads(stream_chunks[1]["choices"][0]["delta"]["content"])

    assert stream_content == non_stream_content


@pytest.mark.parametrize(
    ("payload", "code", "status"),
    [
        (
            {"model": "gpt-4.1", "messages": []},
            "model_not_found",
            404,
        ),
        (
            {"model": "celeba-face-similarity-cpu", "messages": []},
            "image_required",
            400,
        ),
        (
            {
                "model": "celeba-face-similarity-cpu",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": make_image_data_url("JPEG")},
                            },
                            {"type": "image_url", "image_url": {"url": make_image_data_url("PNG")}},
                        ],
                    }
                ],
            },
            "multiple_images_not_supported",
            400,
        ),
        (
            {
                "model": "celeba-face-similarity-cpu",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": "https://example.com/image.jpg"},
                            },
                        ],
                    }
                ],
            },
            "remote_image_url_not_supported",
            400,
        ),
    ],
)
def test_chat_completion_streaming_rejects_request_errors(
    monkeypatch, payload, code, status
) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    client = _streaming_client()

    request_payload = dict(payload)
    request_payload["stream"] = True
    response = client.post("/v1/chat/completions", headers=_auth_headers(), json=request_payload)

    assert response.status_code == status
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["error"]["code"] == code


def test_chat_completion_streaming_rejects_missing_auth(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    client = _streaming_client()

    response = client.post(
        "/v1/chat/completions",
        json=_chat_request(make_image_data_url("JPEG"), stream=True),
    )

    assert response.status_code == 401
    assert response.headers["content-type"].startswith("application/json")


def test_chat_completion_streaming_invalid_image_returns_json_error(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    client = _streaming_client()

    response = client.post(
        "/v1/chat/completions",
        headers=_auth_headers(),
        json=_chat_request("data:image/jpeg;base64,@@@", stream=True),
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_image_base64"


def test_chat_completion_streaming_engine_not_ready_returns_json_error(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    client = _build_streaming_app(detector=None, embedder=None, gallery_store=None)

    response = client.post(
        "/v1/chat/completions",
        headers=_auth_headers(),
        json=_chat_request(make_image_data_url("JPEG"), stream=True),
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "engine_not_ready"
