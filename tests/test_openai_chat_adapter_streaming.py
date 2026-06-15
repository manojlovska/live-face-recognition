from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from tests.image_helpers import make_image_data_url
from tests.test_chat_completions_streaming import (
    ChatRuntime,
    FakeSFaceEmbedder,
    FakeYuNetDetector,
    _build_app,
    _build_gallery_store,
    _face_row,
)


def test_openai_sdk_can_stream_local_chat_completions(monkeypatch) -> None:
    openai = pytest.importorskip("openai")

    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    http_client = TestClient(
        _build_app(
            ChatRuntime(
                detector=FakeYuNetDetector(_face_row()),
                embedder=FakeSFaceEmbedder(),
                gallery_store=_build_gallery_store(),
            )
        )
    )
    client = openai.OpenAI(
        api_key="local-dev-key",
        base_url=f"{str(http_client.base_url).rstrip('/')}/v1",
        http_client=http_client,
    )

    try:
        stream = client.chat.completions.create(
            model="celeba-face-similarity-cpu",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Who is this face most similar to?"},
                        {
                            "type": "image_url",
                            "image_url": {"url": make_image_data_url("JPEG")},
                        },
                    ],
                }
            ],
            stream=True,
        )

        chunks = list(stream)
    finally:
        client.close()
        http_client.close()

    assert chunks
    assert chunks[0].choices[0].delta.role == "assistant"

    content_chunks = [chunk for chunk in chunks if chunk.choices[0].delta.content]
    assert content_chunks
    content = json.loads(content_chunks[0].choices[0].delta.content)
    assert content["result_type"] == "face_similarity"
    assert content["mode"] == "similarity"
    assert "data:image" not in content_chunks[0].choices[0].delta.content
