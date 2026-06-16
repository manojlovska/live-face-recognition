from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_dockerfile_exists_and_is_cpu_only() -> None:
    dockerfile = ROOT / "Dockerfile"
    assert dockerfile.exists()

    text = _read_text(dockerfile)
    lowered = text.lower()

    assert "cuda" not in lowered
    assert "nvidia" not in lowered
    assert "pytorch" not in lowered
    assert "tensorflow" not in lowered
    assert "gpu" not in lowered
    assert "face_api_key" not in lowered
    assert "python:3.12-slim" in lowered
    assert "uvicorn" in lowered
    assert "0.0.0.0" in text
    assert "8000" in text
    assert "useradd" in lowered or "user " in lowered
    assert "appuser" in lowered
    assert "healthz" in lowered


def test_dockerignore_excludes_sensitive_and_generated_files() -> None:
    dockerignore = ROOT / ".dockerignore"
    assert dockerignore.exists()

    text = _read_text(dockerignore)
    assert ".env" in text
    assert "models/*" in text
    assert "!models/.gitkeep" in text
    assert "data/gallery/*" in text
    assert "reports/*" in text
    assert "!reports/.gitkeep" in text
    assert "!data/gallery/.gitkeep" in text
    assert "*.npy" in text
    assert "*.sqlite" in text
    assert "*.db" in text


def test_no_optional_compose_file_or_safe_if_present() -> None:
    compose = ROOT / "docker-compose.example.yml"
    if not compose.exists():
        return

    text = _read_text(compose).lower()
    assert "postgres" not in text
    assert "redis" not in text
    assert "celery" not in text
    assert "face_api_key" not in text or "change-me" in text
