from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.api.errors import ChatCompletionsError
from app.config import Settings, get_settings
from app.main import create_app
from app.services.face_similarity import FaceSimilarityEngine
from app.services.gallery import GalleryStore
from app.services.openai_chat_adapter import parse_chat_completion_request
from tests.image_helpers import make_image_data_url

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "gallery"


class FakeYuNetDetector:
    def __init__(self, faces: np.ndarray) -> None:
        self.faces = faces
        self.input_size: tuple[int, int] | None = None

    def setInputSize(self, size: tuple[int, int]) -> None:  # noqa: N802 - OpenCV API
        self.input_size = tuple(size)

    def detect(self, _image: np.ndarray) -> tuple[None, np.ndarray]:
        return None, self.faces


class FakeSFaceEmbedder:
    def __init__(self, feature_dim: int = 128) -> None:
        self.feature_vector = np.arange(1, feature_dim + 1, dtype=np.float32)

    def alignCrop(self, image: np.ndarray, _face: np.ndarray) -> np.ndarray:  # noqa: N802 - OpenCV API
        return image

    def feature(self, _aligned_face: np.ndarray) -> np.ndarray:  # noqa: N802 - OpenCV API
        return self.feature_vector


class ChatRuntime:
    def __init__(
        self,
        detector: object | None,
        embedder: object | None,
        gallery_store: GalleryStore | None,
    ) -> None:
        self._detector = detector
        self._embedder = embedder
        self._gallery_store = gallery_store

    @property
    def model_id(self) -> str:
        return "celeba-face-similarity-cpu"

    def is_ready(self) -> bool:
        return bool(
            self._detector is not None
            and self._embedder is not None
            and self._gallery_store is not None
            and self._gallery_store.is_loaded()
        )

    def detector_state(self) -> str:
        return "loaded" if self._detector is not None else "missing"

    def embedder_state(self) -> str:
        return "loaded" if self._embedder is not None else "missing"

    def get_detector(self) -> object | None:
        return self._detector

    def get_embedder(self) -> object | None:
        return self._embedder

    def get_gallery_store(self) -> GalleryStore | None:
        return self._gallery_store

    def status(self) -> dict[str, object]:
        gallery_details = self._gallery_store.status() if self._gallery_store is not None else {}
        gallery_state = gallery_details.get("state", "missing")
        return {
            "ready": self.is_ready(),
            "models": {
                "detector": self.detector_state(),
                "embedder": self.embedder_state(),
            },
            "gallery": gallery_state,
            "load_error": None,
            "errors": {
                "detector": None,
                "embedder": None,
            },
            "load_attempted": True,
            "cpu_only": True,
            "opencv_available": True,
            "assets": {},
            "gallery_details": gallery_details,
        }

    def readiness_summary(self) -> dict[str, object]:
        gallery_details = self._gallery_store.status() if self._gallery_store is not None else {}
        if self._detector is None:
            models_state = "models_missing"
        elif self._embedder is None:
            models_state = "detection_only"
        elif self._gallery_store is not None and self._gallery_store.is_loaded():
            models_state = "loaded"
        elif self._gallery_store is not None:
            models_state = "embedding_models_loaded_gallery_missing"
        else:
            models_state = "embedding_only"
        return {
            "models": models_state,
            "gallery": gallery_details.get("state", "missing"),
            "assets": {},
            "gallery_details": gallery_details,
            "load_error": None,
        }


def _build_gallery_store() -> GalleryStore:
    settings = Settings(
        gallery_dir=str(FIXTURE_DIR),
        gallery_embeddings_path=str(FIXTURE_DIR / "gallery_embeddings.npy"),
        gallery_metadata_path=str(FIXTURE_DIR / "gallery_metadata.jsonl"),
        gallery_manifest_path=str(FIXTURE_DIR / "gallery_manifest.json"),
    )
    store = GalleryStore(settings)
    store.load()
    return store


def _face_row() -> np.ndarray:
    return np.array(
        [
            [
                100.4,
                80.1,
                220.0,
                220.0,
                150.0,
                130.0,
                190.0,
                130.0,
                170.0,
                155.0,
                152.0,
                185.0,
                188.0,
                185.0,
                0.97,
            ]
        ],
        dtype=np.float32,
    )


def _build_app(runtime: ChatRuntime) -> object:
    get_settings.cache_clear()
    app = create_app()
    app.state.model_runtime = runtime
    app.state.face_similarity_engine = FaceSimilarityEngine(runtime)
    return app


def _auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer local-dev-key"}


def _chat_request(
    image_url: str,
    *,
    top_k: int = 5,
    stream: bool | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "model": "celeba-face-similarity-cpu",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Who is this face most similar to?"},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ],
        "top_k": top_k,
    }
    if stream is not None:
        payload["stream"] = stream
    return payload


def test_parse_chat_completion_request_accepts_supported_request(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    settings = Settings(model_id="celeba-face-similarity-cpu")

    request = parse_chat_completion_request(
        {
            "model": "celeba-face-similarity-cpu",
            "messages": [
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
            "top_k": 7,
        },
        settings=settings,
    )

    assert request.model == "celeba-face-similarity-cpu"
    assert request.top_k == 7
    assert request.image_data_url.startswith("data:image/jpeg;base64,")


def test_parse_chat_completion_request_rejects_missing_image(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    settings = Settings(model_id="celeba-face-similarity-cpu")

    with pytest.raises(ChatCompletionsError) as excinfo:
        parse_chat_completion_request(
            {
                "model": "celeba-face-similarity-cpu",
                "messages": [{"role": "user", "content": [{"type": "text", "text": "hi"}]}],
            },
            settings=settings,
        )

    assert getattr(excinfo.value, "code", None) == "image_required"


def test_chat_completion_contract_returns_similarity_result(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    client = TestClient(
        _build_app(
            ChatRuntime(
                detector=FakeYuNetDetector(_face_row()),
                embedder=FakeSFaceEmbedder(),
                gallery_store=_build_gallery_store(),
            )
        )
    )

    response = client.post(
        "/v1/chat/completions",
        headers=_auth_headers(),
        json=_chat_request(make_image_data_url("JPEG"), top_k=2),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["object"] == "chat.completion"
    assert body["choices"][0]["message"]["role"] == "assistant"
    content = json.loads(body["choices"][0]["message"]["content"])
    assert content["result_type"] == "face_similarity"
    assert content["mode"] == "similarity"
    assert content["gallery"] == {
        "state": "loaded",
        "version": "test-gallery-v1",
        "item_count": 3,
        "embedding_dim": 128,
    }
    assert content["faces"][0]["top_matches"]
    assert "vector" not in body["choices"][0]["message"]["content"]
    assert "data:image" not in body["choices"][0]["message"]["content"]


def test_chat_completion_contract_preserves_detection_only_when_embedder_missing(
    monkeypatch,
) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    client = TestClient(
        _build_app(
            ChatRuntime(
                detector=FakeYuNetDetector(_face_row()),
                embedder=None,
                gallery_store=None,
            )
        )
    )

    response = client.post(
        "/v1/chat/completions",
        headers=_auth_headers(),
        json=_chat_request(make_image_data_url("PNG"), top_k=5),
    )

    assert response.status_code == 200
    content = json.loads(response.json()["choices"][0]["message"]["content"])
    assert content["mode"] == "detection_only"
    assert content["faces"][0]["top_matches"] == []
    assert "gallery" not in content


def test_chat_completion_contract_rejects_missing_auth(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    client = TestClient(
        _build_app(
            ChatRuntime(
                detector=FakeYuNetDetector(_face_row()),
                embedder=FakeSFaceEmbedder(),
                gallery_store=_build_gallery_store(),
            )
        )
    )

    response = client.post(
        "/v1/chat/completions",
        json=_chat_request(make_image_data_url("JPEG")),
    )

    assert response.status_code == 401


def test_chat_completion_contract_rejects_wrong_auth(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    client = TestClient(
        _build_app(
            ChatRuntime(
                detector=FakeYuNetDetector(_face_row()),
                embedder=FakeSFaceEmbedder(),
                gallery_store=_build_gallery_store(),
            )
        )
    )

    response = client.post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer wrong-key"},
        json=_chat_request(make_image_data_url("JPEG")),
    )

    assert response.status_code == 401


def test_chat_completion_contract_preserves_stream_false(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    client = TestClient(
        _build_app(
            ChatRuntime(
                detector=FakeYuNetDetector(_face_row()),
                embedder=FakeSFaceEmbedder(),
                gallery_store=_build_gallery_store(),
            )
        )
    )

    response = client.post(
        "/v1/chat/completions",
        headers=_auth_headers(),
        json=_chat_request(make_image_data_url("JPEG"), stream=False),
    )

    assert response.status_code == 200
    assert response.json()["object"] == "chat.completion"


def test_chat_completion_contract_rejects_remote_image_url(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    client = TestClient(
        _build_app(
            ChatRuntime(
                detector=FakeYuNetDetector(_face_row()),
                embedder=FakeSFaceEmbedder(),
                gallery_store=_build_gallery_store(),
            )
        )
    )

    response = client.post(
        "/v1/chat/completions",
        headers=_auth_headers(),
        json=_chat_request("https://example.com/image.jpg"),
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "remote_image_url_not_supported"


def test_chat_completion_contract_rejects_multiple_images(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    client = TestClient(
        _build_app(
            ChatRuntime(
                detector=FakeYuNetDetector(_face_row()),
                embedder=FakeSFaceEmbedder(),
                gallery_store=_build_gallery_store(),
            )
        )
    )

    response = client.post(
        "/v1/chat/completions",
        headers=_auth_headers(),
        json={
            "model": "celeba-face-similarity-cpu",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": make_image_data_url("JPEG")}},
                        {"type": "image_url", "image_url": {"url": make_image_data_url("PNG")}},
                    ],
                }
            ],
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "multiple_images_not_supported"


def test_chat_completion_contract_rejects_unsupported_model(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    client = TestClient(
        _build_app(
            ChatRuntime(
                detector=FakeYuNetDetector(_face_row()),
                embedder=FakeSFaceEmbedder(),
                gallery_store=_build_gallery_store(),
            )
        )
    )

    response = client.post(
        "/v1/chat/completions",
        headers=_auth_headers(),
        json={
            "model": "gpt-4.1",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": make_image_data_url("JPEG")}},
                    ],
                }
            ],
        },
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "model_not_found"


def test_chat_completion_contract_reports_native_image_validation_errors(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    client = TestClient(
        _build_app(
            ChatRuntime(
                detector=FakeYuNetDetector(_face_row()),
                embedder=FakeSFaceEmbedder(),
                gallery_store=_build_gallery_store(),
            )
        )
    )

    response = client.post(
        "/v1/chat/completions",
        headers=_auth_headers(),
        json=_chat_request("data:image/jpeg;base64,@@@"),
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_image_base64"


def test_chat_completion_contract_rejects_malformed_content(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    client = TestClient(
        _build_app(
            ChatRuntime(
                detector=FakeYuNetDetector(_face_row()),
                embedder=FakeSFaceEmbedder(),
                gallery_store=_build_gallery_store(),
            )
        )
    )

    response = client.post(
        "/v1/chat/completions",
        headers=_auth_headers(),
        json={
            "model": "celeba-face-similarity-cpu",
            "messages": [{"role": "user", "content": "hello"}],
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_chat_message"


def test_chat_completion_contract_reports_engine_not_ready(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")
    client = TestClient(
        _build_app(
            ChatRuntime(
                detector=None,
                embedder=None,
                gallery_store=None,
            )
        )
    )

    response = client.post(
        "/v1/chat/completions",
        headers=_auth_headers(),
        json=_chat_request(make_image_data_url("JPEG")),
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "engine_not_ready"


def test_openai_sdk_can_call_local_chat_completions(monkeypatch) -> None:
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
        response = client.chat.completions.create(
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
        )
    finally:
        client.close()
        http_client.close()

    content = json.loads(response.choices[0].message.content or "{}")
    assert response.object == "chat.completion"
    assert content["result_type"] == "face_similarity"
    assert content["mode"] == "similarity"
