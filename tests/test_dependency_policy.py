from __future__ import annotations

import tomllib
from pathlib import Path

PYPROJECT_PATH = Path(__file__).resolve().parents[1] / "pyproject.toml"


def _pyproject() -> dict[str, object]:
    return tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))


def test_pyproject_declares_bounded_cpu_only_runtime_dependencies() -> None:
    project = _pyproject()["project"]
    runtime_deps = project["dependencies"]

    assert any(spec.startswith("fastapi>=") and ",<" in spec for spec in runtime_deps)
    assert any(
        spec.startswith("opencv-contrib-python-headless>=") and ",<" in spec
        for spec in runtime_deps
    )
    assert any(spec.startswith("numpy>=") and ",<" in spec for spec in runtime_deps)
    assert any(spec.startswith("Pillow>=") and ",<" in spec for spec in runtime_deps)
    assert any(spec.startswith("pydantic>=") and ",<" in spec for spec in runtime_deps)
    assert any(spec.startswith("pydantic-settings>=") and ",<" in spec for spec in runtime_deps)
    assert any(spec.startswith("uvicorn[standard]>=") and ",<" in spec for spec in runtime_deps)

    forbidden = {
        "cuda",
        "faiss",
        "onnxruntime-gpu",
        "postgresql",
        "redis",
        "tensorflow",
        "torch",
        "celery",
    }
    assert not any(any(token in spec.lower() for token in forbidden) for spec in runtime_deps)


def test_pyproject_separates_dev_and_test_dependencies() -> None:
    optional = _pyproject()["project"]["optional-dependencies"]
    dev_deps = optional["dev"]
    test_deps = optional["test"]

    assert any(spec.startswith("httpx>=") and ",<" in spec for spec in dev_deps)
    assert any(spec.startswith("ruff>=") and ",<" in spec for spec in dev_deps)
    assert not any(spec.startswith("pytest") for spec in dev_deps)
    assert not any(spec.startswith("httpx2") for spec in dev_deps)

    assert any(spec.startswith("httpx2>=") and ",<" in spec for spec in test_deps)
    assert any(spec.startswith("openai>=") and ",<" in spec for spec in test_deps)
    assert any(spec.startswith("pytest>=") and ",<" in spec for spec in test_deps)
    assert any(spec.startswith("pytest-asyncio>=") and ",<" in spec for spec in test_deps)
    assert any(spec.startswith("pytest-cov>=") and ",<" in spec for spec in test_deps)
    assert not any(spec.startswith("httpx>=") for spec in test_deps)


def test_pyproject_does_not_reintroduce_gpu_or_server_dependencies() -> None:
    project = _pyproject()["project"]
    all_specs = list(project["dependencies"])
    optional = project["optional-dependencies"]
    all_specs.extend(optional["dev"])
    all_specs.extend(optional["test"])

    forbidden = [
        "tensorflow",
        "torch",
        "cuda",
        "cudnn",
        "faiss",
        "postgresql",
        "redis",
        "celery",
        "selenium",
        "playwright",
        "docker",
    ]
    assert not any(any(token in spec.lower() for token in forbidden) for spec in all_specs)
