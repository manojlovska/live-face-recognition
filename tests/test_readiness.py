from fastapi.testclient import TestClient

from app.main import app


def test_readyz_returns_not_ready() -> None:
    client = TestClient(app)

    response = client.get("/readyz")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "service": "CelebA Face Similarity API",
        "version": "0.0.0",
        "checks": {
            "api": "ok",
            "models": "not_loaded",
            "gallery": "not_loaded",
        },
    }
