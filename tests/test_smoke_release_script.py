from __future__ import annotations

import base64
import json
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app
from scripts import smoke_release
from scripts._client_utils import make_tiny_image_data_url, write_json_report
from tests.test_openai_chat_adapter import (
    ChatRuntime,
    FakeSFaceEmbedder,
    FakeYuNetDetector,
    _build_app,
    _build_gallery_store,
    _face_row,
)


def _default_client() -> TestClient:
    get_settings.cache_clear()
    return TestClient(create_app())


def _ready_client() -> TestClient:
    get_settings.cache_clear()
    return TestClient(
        _build_app(
            ChatRuntime(
                detector=FakeYuNetDetector(_face_row()),
                embedder=FakeSFaceEmbedder(),
                gallery_store=_build_gallery_store(),
            )
        )
    )


def test_generated_image_data_url_is_valid_and_self_contained() -> None:
    data_url = make_tiny_image_data_url("JPEG")

    assert data_url.startswith("data:image/jpeg;base64,")
    encoded_payload = data_url.split(",", 1)[1]
    assert base64.b64decode(encoded_payload)


def test_smoke_checks_report_not_ready_as_operational(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")

    with _default_client() as client:
        report = smoke_release.run_smoke_checks(
            client,
            api_key="local-dev-key",
            base_url="http://testserver",
        )

    assert report["readiness_status"] == "not_ready"
    assert report["service_status"] == "operational"
    assert report["checks"]["healthz"]["ok"] is True
    assert report["checks"]["readyz"]["ok"] is True
    assert report["checks"]["models_missing_auth"]["ok"] is True
    assert report["checks"]["native_missing_auth"]["ok"] is True
    assert report["checks"]["demo"]["ok"] is True


def test_smoke_checks_report_ready_when_local_runtime_is_ready(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")

    with _ready_client() as client:
        report = smoke_release.run_smoke_checks(
            client,
            api_key="local-dev-key",
            base_url="http://testserver",
        )

    assert report["readiness_status"] == "ready"
    assert report["service_status"] == "ready"
    assert report["checks"]["readyz"]["status_code"] == 200


def test_smoke_output_omits_sensitive_values(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")

    with _default_client() as client:
        report = smoke_release.run_smoke_checks(
            client,
            api_key="local-dev-key",
            base_url="http://testserver",
        )

    output_path = tmp_path / "smoke-release.json"
    write_json_report(output_path, report)

    text = output_path.read_text(encoding="utf-8")
    assert "local-dev-key" not in text
    assert "data:image" not in text


def test_smoke_parser_help_exits_cleanly(capsys) -> None:
    with pytest.raises(SystemExit) as excinfo:
        smoke_release.build_parser().parse_args(["--help"])

    assert excinfo.value.code == 0
    assert "Run local release smoke checks." in capsys.readouterr().out


def test_smoke_script_runs_help_from_temp_cwd(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "smoke_release.py"
    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Run local release smoke checks." in result.stdout


def test_smoke_main_writes_json_report(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")

    def _client_factory(*_args, **_kwargs) -> TestClient:
        return _default_client()

    monkeypatch.setattr(smoke_release.httpx, "Client", _client_factory)

    output_path = tmp_path / "smoke-report.json"
    exit_code = smoke_release.main(
        [
            "--base-url",
            "http://testserver",
            "--api-key",
            "local-dev-key",
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["readiness_status"] == "not_ready"
    assert "local-dev-key" not in output_path.read_text(encoding="utf-8")
    assert "data:image" not in output_path.read_text(encoding="utf-8")


def test_smoke_checks_include_sanitized_startup_diagnostics(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")

    with _default_client() as client:
        report = smoke_release.run_smoke_checks(
            client,
            api_key="local-dev-key",
            base_url="http://testserver",
            check_diagnostics=True,
        )

    assert report["diagnostics"]["available"] is True
    assert report["diagnostics"]["status"] == "ok"
    assert report["diagnostics"]["summary"] == {"errors": 0, "warnings": 0}
