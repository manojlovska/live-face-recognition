from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

if __package__ in {None, ""}:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx

from scripts._client_utils import (
    count_values,
    extract_chat_completion_content,
    extract_native_result_mode,
    extract_stream_result_mode,
    make_image_data_url_from_file,
    make_tiny_image_data_url,
    summarize_latencies,
    write_json_report,
)

TARGET_CHOICES = ("native", "chat", "chat-stream", "all")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark local API endpoints.")
    parser.add_argument("--base-url", required=True, help="Local service base URL.")
    parser.add_argument("--api-key", required=True, help="Bearer token for protected routes.")
    parser.add_argument(
        "--endpoint",
        choices=TARGET_CHOICES,
        required=True,
        help="Benchmark target.",
    )
    parser.add_argument(
        "--requests",
        type=_positive_int,
        default=20,
        help="Recorded requests per target.",
    )
    parser.add_argument(
        "--warmup",
        type=_nonnegative_int,
        default=3,
        help="Warmup requests per target.",
    )
    parser.add_argument(
        "--image-file",
        type=Path,
        default=None,
        help="Optional image file to benchmark instead of the generated tiny image.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional JSON report path.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Per-request timeout in seconds.",
    )
    return parser


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def _nonnegative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be at least 0")
    return parsed


def _auth_headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}"}


def _safe_json(response: Any) -> dict[str, Any] | None:
    try:
        body = response.json()
    except Exception:  # noqa: BLE001 - local benchmark script must tolerate non-JSON failures
        return None
    return body if isinstance(body, dict) else None


def _image_data_url(image_file: Path | None) -> str:
    if image_file is None:
        return make_tiny_image_data_url("JPEG")
    return make_image_data_url_from_file(image_file)


def _base_result(
    *,
    target: str,
    requests: int,
    warmup: int,
    base_url: str,
    started_at: str,
    finished_at: str,
    notes: list[str],
) -> dict[str, Any]:
    return {
        "target": target,
        "requests": requests,
        "warmup": warmup,
        "base_url": base_url.rstrip("/"),
        "started_at": started_at,
        "finished_at": finished_at,
        "notes": notes,
    }


def _measure_request(
    call: Callable[[], tuple[int, str | None, float, float | None]],
) -> tuple[int, str | None, float, float | None]:
    return call()


def _run_native(
    client: Any,
    *,
    api_key: str,
    requests: int,
    warmup: int,
    base_url: str,
    image_data_url: str,
) -> dict[str, Any]:
    statuses: list[str] = []
    modes: list[str] = []
    latencies: list[float] = []
    notes: list[str] = []
    broken = False
    started_at = datetime.now(UTC).isoformat()

    def call() -> tuple[int, str | None, float, float | None]:
        payload = {
            "image": image_data_url,
            "top_k": 5,
            "return_face_boxes": True,
        }
        started = perf_counter()
        response = client.post("/v1/face/similarity", headers=_auth_headers(api_key), json=payload)
        elapsed_ms = (perf_counter() - started) * 1000.0
        body = _safe_json(response)
        mode = extract_native_result_mode(body) if body is not None else None
        return response.status_code, mode, elapsed_ms, None

    for index in range(warmup + requests):
        try:
            status_code, mode, latency_ms, _first_chunk_ms = _measure_request(call)
        except Exception as exc:  # noqa: BLE001
            broken = True
            notes.append(f"native request {index + 1} failed: {exc.__class__.__name__}")
            continue

        if index < warmup:
            continue

        statuses.append(str(status_code))
        latencies.append(latency_ms)
        if mode is None:
            broken = True
            notes.append("native response did not include a recognizable result mode.")
            continue

        modes.append(mode)
        if status_code == 503 and mode == "engine_not_ready":
            notes.append("native endpoint returned engine_not_ready.")
        elif status_code == 200 and mode not in {"similarity", "detection_only", "embedding_only"}:
            broken = True
            notes.append(f"native endpoint returned unexpected result mode: {mode}.")
        elif status_code not in {200, 503}:
            broken = True
            notes.append(f"native endpoint returned unexpected status: {status_code}.")

    finished_at = datetime.now(UTC).isoformat()
    report = _base_result(
        target="native",
        requests=requests,
        warmup=warmup,
        base_url=base_url,
        started_at=started_at,
        finished_at=finished_at,
        notes=notes,
    )
    report["latency_ms"] = summarize_latencies(latencies)
    report["status_counts"] = count_values(statuses)
    report["result_modes"] = count_values(modes)
    report["benchmark_status"] = "broken" if broken else "ok"
    return report


def _run_chat(
    client: Any,
    *,
    api_key: str,
    requests: int,
    warmup: int,
    base_url: str,
    image_data_url: str,
) -> dict[str, Any]:
    statuses: list[str] = []
    modes: list[str] = []
    latencies: list[float] = []
    notes: list[str] = []
    broken = False
    started_at = datetime.now(UTC).isoformat()

    def call() -> tuple[int, str | None, float, float | None]:
        payload = {
            "model": "celeba-face-similarity-cpu",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Who is this face most similar to?"},
                        {"type": "image_url", "image_url": {"url": image_data_url}},
                    ],
                }
            ],
            "top_k": 5,
        }
        started = perf_counter()
        response = client.post("/v1/chat/completions", headers=_auth_headers(api_key), json=payload)
        elapsed_ms = (perf_counter() - started) * 1000.0
        body = _safe_json(response)
        mode = None
        if body is not None:
            content_payload = extract_chat_completion_content(body)
            if content_payload is not None:
                mode = extract_native_result_mode(content_payload)
        return response.status_code, mode, elapsed_ms, None

    for index in range(warmup + requests):
        try:
            status_code, mode, latency_ms, _first_chunk_ms = _measure_request(call)
        except Exception as exc:  # noqa: BLE001
            broken = True
            notes.append(f"chat request {index + 1} failed: {exc.__class__.__name__}")
            continue

        if index < warmup:
            continue

        statuses.append(str(status_code))
        latencies.append(latency_ms)
        if mode is None:
            broken = True
            notes.append("chat response did not include a recognizable result mode.")
            continue

        modes.append(mode)
        if status_code == 503 and mode == "engine_not_ready":
            notes.append("chat completions returned engine_not_ready.")
        elif status_code == 200 and mode not in {"similarity", "detection_only", "embedding_only"}:
            broken = True
            notes.append(f"chat completions returned unexpected result mode: {mode}.")
        elif status_code not in {200, 503}:
            broken = True
            notes.append(f"chat completions returned unexpected status: {status_code}.")

    finished_at = datetime.now(UTC).isoformat()
    report = _base_result(
        target="chat",
        requests=requests,
        warmup=warmup,
        base_url=base_url,
        started_at=started_at,
        finished_at=finished_at,
        notes=notes,
    )
    report["latency_ms"] = summarize_latencies(latencies)
    report["status_counts"] = count_values(statuses)
    report["result_modes"] = count_values(modes)
    report["benchmark_status"] = "broken" if broken else "ok"
    return report


def _run_chat_stream(
    client: Any,
    *,
    api_key: str,
    requests: int,
    warmup: int,
    base_url: str,
    image_data_url: str,
) -> dict[str, Any]:
    statuses: list[str] = []
    modes: list[str] = []
    latencies: list[float] = []
    first_chunk_latencies: list[float] = []
    notes: list[str] = []
    broken = False
    started_at = datetime.now(UTC).isoformat()

    def call() -> tuple[int, str | None, float, float | None]:
        payload = {
            "model": "celeba-face-similarity-cpu",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Who is this face most similar to?"},
                        {"type": "image_url", "image_url": {"url": image_data_url}},
                    ],
                }
            ],
            "top_k": 5,
            "stream": True,
        }
        started = perf_counter()
        first_chunk_ms: float | None = None
        with client.stream(
            "POST",
            "/v1/chat/completions",
            headers=_auth_headers(api_key),
            json=payload,
        ) as response:
            body_parts: list[str] = []
            for text in response.iter_text():
                if text and first_chunk_ms is None:
                    first_chunk_ms = (perf_counter() - started) * 1000.0
                body_parts.append(text)
            total_ms = (perf_counter() - started) * 1000.0
            body = "".join(body_parts)
            mode = None
            if response.status_code == 200:
                mode = extract_stream_result_mode(body)
            else:
                try:
                    body_json = json.loads(body) if body else None
                except json.JSONDecodeError:
                    body_json = None
                if body_json is not None:
                    mode = extract_native_result_mode(body_json)
            return response.status_code, mode, total_ms, first_chunk_ms

    for index in range(warmup + requests):
        try:
            status_code, mode, latency_ms, first_chunk_ms = _measure_request(call)
        except Exception as exc:  # noqa: BLE001
            broken = True
            notes.append(f"chat-stream request {index + 1} failed: {exc.__class__.__name__}")
            continue

        if index < warmup:
            continue

        statuses.append(str(status_code))
        latencies.append(latency_ms)
        if first_chunk_ms is not None:
            first_chunk_latencies.append(first_chunk_ms)

        if mode is None:
            broken = True
            notes.append("chat-stream response did not include a recognizable result mode.")
            continue

        modes.append(mode)
        if status_code == 503 and mode == "engine_not_ready":
            notes.append("chat-stream returned engine_not_ready.")
        elif status_code == 200 and mode not in {"similarity", "detection_only", "embedding_only"}:
            broken = True
            notes.append(f"chat-stream returned unexpected result mode: {mode}.")
        elif status_code not in {200, 503}:
            broken = True
            notes.append(f"chat-stream returned unexpected status: {status_code}.")

    finished_at = datetime.now(UTC).isoformat()
    report = _base_result(
        target="chat-stream",
        requests=requests,
        warmup=warmup,
        base_url=base_url,
        started_at=started_at,
        finished_at=finished_at,
        notes=notes,
    )
    report["latency_ms"] = summarize_latencies(latencies)
    report["stream_first_chunk_ms"] = summarize_latencies(first_chunk_latencies)
    report["status_counts"] = count_values(statuses)
    report["result_modes"] = count_values(modes)
    report["benchmark_status"] = "broken" if broken else "ok"
    return report


def run_benchmark(
    client: Any,
    *,
    api_key: str,
    base_url: str,
    endpoint: str,
    requests: int,
    warmup: int,
    image_file: Path | None = None,
) -> dict[str, Any]:
    image_data_url = _image_data_url(image_file)
    run_map = {
        "native": _run_native,
        "chat": _run_chat,
        "chat-stream": _run_chat_stream,
    }

    if endpoint == "all":
        runs = [
            run_map[target](
                client,
                api_key=api_key,
                requests=requests,
                warmup=warmup,
                base_url=base_url,
                image_data_url=image_data_url,
            )
            for target in ("native", "chat", "chat-stream")
        ]
        return {
            "target": "all",
            "requests": requests,
            "warmup": warmup,
            "base_url": base_url.rstrip("/"),
            "started_at": min(run["started_at"] for run in runs),
            "finished_at": max(run["finished_at"] for run in runs),
            "runs": runs,
            "notes": [note for run in runs for note in run["notes"]],
            "benchmark_status": "broken"
            if any(run["benchmark_status"] == "broken" for run in runs)
            else "ok",
        }

    return run_map[endpoint](
        client,
        api_key=api_key,
        requests=requests,
        warmup=warmup,
        base_url=base_url,
        image_data_url=image_data_url,
    )


def format_benchmark_report(report: dict[str, Any]) -> str:
    if report["target"] == "all":
        lines = [
            f"target: {report['target']}",
            f"benchmark_status: {report['benchmark_status']}",
        ]
        for run in report["runs"]:
            lines.append(
                f"- {run['target']}: {run['benchmark_status']}, "
                f"latency={run['latency_ms']}, status={run['status_counts']}",
            )
            if "stream_first_chunk_ms" in run:
                lines.append(f"  stream_first_chunk_ms={run['stream_first_chunk_ms']}")
        return "\n".join(lines)

    lines = [
        f"target: {report['target']}",
        f"benchmark_status: {report['benchmark_status']}",
        f"latency_ms: {report['latency_ms']}",
        f"status_counts: {report['status_counts']}",
        f"result_modes: {report['result_modes']}",
    ]
    if "stream_first_chunk_ms" in report:
        lines.append(f"stream_first_chunk_ms: {report['stream_first_chunk_ms']}")
    if report["notes"]:
        lines.append("notes:")
        lines.extend(f"  - {note}" for note in report["notes"])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    with httpx.Client(base_url=args.base_url, timeout=args.timeout) as client:
        report = run_benchmark(
            client,
            api_key=args.api_key,
            base_url=args.base_url,
            endpoint=args.endpoint,
            requests=args.requests,
            warmup=args.warmup,
            image_file=args.image_file,
        )

    if args.output is not None:
        write_json_report(args.output, report)

    print(format_benchmark_report(report))
    return 0 if report["benchmark_status"] != "broken" else 1


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
