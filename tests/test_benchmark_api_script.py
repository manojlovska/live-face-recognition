from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app
from scripts import benchmark_api
from scripts._client_utils import (
    count_values,
    extract_chat_completion_content,
    extract_native_result_mode,
    extract_stream_result_mode,
    summarize_latencies,
)


def _client() -> TestClient:
    get_settings.cache_clear()
    return TestClient(create_app())


def test_latency_summary_and_status_counts() -> None:
    summary = summarize_latencies([10.0, 20.0, 30.0, 40.0])
    counts = count_values(["200", "200", "503"])

    assert summary["min"] == 10.0
    assert summary["mean"] == 25.0
    assert summary["median"] == 25.0
    assert summary["p95"] == pytest.approx(38.5)
    assert summary["max"] == 40.0
    assert counts == {"200": 2, "503": 1}


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"mode": "similarity"}, "similarity"),
        ({"mode": "detection_only"}, "detection_only"),
        ({"mode": "embedding_only"}, "embedding_only"),
        ({"error": {"code": "engine_not_ready"}}, "engine_not_ready"),
        (
            {
                "object": "chat.completion",
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {"result_type": "face_similarity", "mode": "similarity"}
                            )
                        }
                    }
                ],
            },
            "similarity",
        ),
    ],
)
def test_result_mode_extraction_handles_native_and_chat_variants(payload, expected) -> None:
    native_mode = extract_native_result_mode(payload)
    chat_content = extract_chat_completion_content(payload)

    if payload.get("object") == "chat.completion":
        assert chat_content is not None
        assert native_mode is None
        assert extract_native_result_mode(chat_content) == expected
    else:
        assert native_mode == expected


def test_result_mode_extraction_handles_stream_chunks() -> None:
    assistant_chunk = (
        'data: {"id":"chatcmpl-local-1","object":"chat.completion.chunk",'
        '"choices":[{"delta":{"role":"assistant"}}]}'
    )
    content_chunk = (
        'data: {"id":"chatcmpl-local-1","object":"chat.completion.chunk",'
        '"choices":[{"delta":{"content":"{\\"result_type\\": \\"face_similarity\\", '
        '\\"mode\\": \\"similarity\\"}"}}]}'
    )
    stream_body = "\n".join(
        [
            assistant_chunk,
            "",
            content_chunk,
            "",
            "data: [DONE]",
            "",
        ]
    )

    assert extract_stream_result_mode(stream_body) == "similarity"


def test_benchmark_run_native_omits_sensitive_values(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")

    with _client() as client:
        report = benchmark_api.run_benchmark(
            client,
            api_key="local-dev-key",
            base_url="http://testserver",
            endpoint="native",
            requests=1,
            warmup=0,
        )

    assert report["target"] == "native"
    assert report["benchmark_status"] == "ok"
    assert report["result_modes"]

    serialized = json.dumps(report)
    assert "local-dev-key" not in serialized
    assert "data:image" not in serialized


def test_benchmark_run_all_returns_each_target(monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")

    with _client() as client:
        report = benchmark_api.run_benchmark(
            client,
            api_key="local-dev-key",
            base_url="http://testserver",
            endpoint="all",
            requests=1,
            warmup=0,
        )

    assert report["target"] == "all"
    assert len(report["runs"]) == 3
    assert {run["target"] for run in report["runs"]} == {"native", "chat", "chat-stream"}


def test_benchmark_parser_rejects_invalid_endpoint() -> None:
    with pytest.raises(SystemExit):
        benchmark_api.build_parser().parse_args(
            [
                "--base-url",
                "http://localhost:8000",
                "--api-key",
                "local-dev-key",
                "--endpoint",
                "bogus",
            ]
        )


def test_benchmark_parser_help_exits_cleanly(capsys) -> None:
    with pytest.raises(SystemExit) as excinfo:
        benchmark_api.build_parser().parse_args(["--help"])

    assert excinfo.value.code == 0
    assert "Benchmark local API endpoints." in capsys.readouterr().out


def test_benchmark_main_writes_json_report(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("FACE_API_KEY", "local-dev-key")

    def _client_factory(*_args, **_kwargs) -> TestClient:
        return _client()

    monkeypatch.setattr(benchmark_api.httpx, "Client", _client_factory)

    output_path = tmp_path / "benchmark.json"
    exit_code = benchmark_api.main(
        [
            "--base-url",
            "http://testserver",
            "--api-key",
            "local-dev-key",
            "--endpoint",
            "native",
            "--requests",
            "1",
            "--warmup",
            "0",
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    text = output_path.read_text(encoding="utf-8")
    assert "local-dev-key" not in text
    assert "data:image" not in text
