from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx

from scripts._client_utils import (
    extract_chat_completion_content,
    extract_native_result_mode,
    extract_startup_diagnostics_summary,
    extract_stream_result_mode,
    make_tiny_image_data_url,
    write_json_report,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run local release smoke checks.")
    parser.add_argument("--base-url", required=True, help="Local service base URL.")
    parser.add_argument("--api-key", required=True, help="Bearer token for protected routes.")
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
    parser.add_argument(
        "--check-diagnostics",
        action="store_true",
        help="Optionally check the protected startup diagnostics endpoint.",
    )
    return parser


def _auth_headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}"}


def _safe_json(response: Any) -> dict[str, Any] | None:
    try:
        body = response.json()
    except Exception:  # noqa: BLE001 - local smoke script must tolerate non-JSON failures
        return None
    return body if isinstance(body, dict) else None


def _check_demo_page(body: str) -> bool:
    return "CelebA Face Similarity Demo" in body and 'href="/static/demo.css"' in body


def _record_check(
    *,
    name: str,
    ok: bool,
    status_code: int | None,
    detail: str,
    checks: dict[str, dict[str, Any]],
) -> None:
    checks[name] = {
        "ok": ok,
        "status_code": status_code,
        "detail": detail,
    }


def run_smoke_checks(
    client: Any,
    *,
    api_key: str,
    base_url: str,
    check_diagnostics: bool = False,
) -> dict[str, Any]:
    image_data_url = make_tiny_image_data_url("JPEG")
    checks: dict[str, dict[str, Any]] = {}
    notes: list[str] = []
    readiness_status = "unknown"
    service_status = "operational"
    diagnostics: dict[str, Any] | None = None

    try:
        health_response = client.get("/healthz")
        _record_check(
            name="healthz",
            ok=health_response.status_code == 200,
            status_code=health_response.status_code,
            detail=health_response.text[:200],
            checks=checks,
        )
        if health_response.status_code != 200:
            service_status = "broken"
    except Exception as exc:  # noqa: BLE001
        service_status = "broken"
        _record_check(
            name="healthz",
            ok=False,
            status_code=None,
            detail=f"request_failed: {exc.__class__.__name__}",
            checks=checks,
        )

    try:
        ready_response = client.get("/readyz")
        ready_body = _safe_json(ready_response)
        if ready_response.status_code == 200 and isinstance(ready_body, dict):
            readiness_status = str(ready_body.get("status", "ready"))
            ok = readiness_status == "ready"
            detail = readiness_status
        elif ready_response.status_code == 503 and isinstance(ready_body, dict):
            readiness_status = str(ready_body.get("status", "not_ready"))
            ok = readiness_status == "not_ready"
            detail = readiness_status
            if ok:
                notes.append("Service is operational but not fully ready locally.")
        else:
            ok = False
            detail = "invalid_readiness_response"
            service_status = "broken"
        _record_check(
            name="readyz",
            ok=ok,
            status_code=ready_response.status_code,
            detail=detail,
            checks=checks,
        )
        if not ok:
            service_status = "broken"
    except Exception as exc:  # noqa: BLE001
        service_status = "broken"
        _record_check(
            name="readyz",
            ok=False,
            status_code=None,
            detail=f"request_failed: {exc.__class__.__name__}",
            checks=checks,
        )

    try:
        models_missing_auth = client.get("/v1/models")
        models_missing_auth_ok = models_missing_auth.status_code == 401
        if not models_missing_auth_ok:
            service_status = "broken"
        _record_check(
            name="models_missing_auth",
            ok=models_missing_auth_ok,
            status_code=models_missing_auth.status_code,
            detail="missing auth rejected" if models_missing_auth_ok else "expected 401",
            checks=checks,
        )
    except Exception as exc:  # noqa: BLE001
        service_status = "broken"
        _record_check(
            name="models_missing_auth",
            ok=False,
            status_code=None,
            detail=f"request_failed: {exc.__class__.__name__}",
            checks=checks,
        )

    try:
        models_auth = client.get("/v1/models", headers=_auth_headers(api_key))
        models_body = _safe_json(models_auth)
        models_ok = (
            models_auth.status_code == 200
            and isinstance(models_body, dict)
            and isinstance(models_body.get("data"), list)
            and bool(models_body.get("data"))
        )
        if not models_ok:
            service_status = "broken"
        _record_check(
            name="models_auth",
            ok=models_ok,
            status_code=models_auth.status_code,
            detail="ok" if models_ok else "invalid models response",
            checks=checks,
        )
    except Exception as exc:  # noqa: BLE001
        service_status = "broken"
        _record_check(
            name="models_auth",
            ok=False,
            status_code=None,
            detail=f"request_failed: {exc.__class__.__name__}",
            checks=checks,
        )

    try:
        native_missing_auth = client.post("/v1/face/similarity", json={"image": image_data_url})
        native_missing_auth_ok = native_missing_auth.status_code == 401
        if not native_missing_auth_ok:
            service_status = "broken"
        _record_check(
            name="native_missing_auth",
            ok=native_missing_auth_ok,
            status_code=native_missing_auth.status_code,
            detail="missing auth rejected" if native_missing_auth_ok else "expected 401",
            checks=checks,
        )
    except Exception as exc:  # noqa: BLE001
        service_status = "broken"
        _record_check(
            name="native_missing_auth",
            ok=False,
            status_code=None,
            detail=f"request_failed: {exc.__class__.__name__}",
            checks=checks,
        )

    try:
        native_ready = client.post(
            "/v1/face/similarity",
            headers=_auth_headers(api_key),
            json={
                "image": image_data_url,
                "top_k": 5,
                "return_face_boxes": True,
            },
        )
        native_body = _safe_json(native_ready)
        native_mode = extract_native_result_mode(native_body) if native_body is not None else None
        native_ok = False
        if native_ready.status_code == 200 and native_mode in {
            "similarity",
            "detection_only",
            "embedding_only",
        }:
            native_ok = True
        elif native_ready.status_code == 503 and native_mode == "engine_not_ready":
            native_ok = True
            notes.append("Native endpoint returned engine_not_ready for the local environment.")
        else:
            service_status = "broken"
        _record_check(
            name="native_auth",
            ok=native_ok,
            status_code=native_ready.status_code,
            detail=native_mode or "invalid native response",
            checks=checks,
        )
    except Exception as exc:  # noqa: BLE001
        service_status = "broken"
        _record_check(
            name="native_auth",
            ok=False,
            status_code=None,
            detail=f"request_failed: {exc.__class__.__name__}",
            checks=checks,
        )

    try:
        chat_ready = client.post(
            "/v1/chat/completions",
            headers=_auth_headers(api_key),
            json={
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
            },
        )
        chat_body = _safe_json(chat_ready)
        chat_mode = None
        if chat_body is not None:
            content_payload = extract_chat_completion_content(chat_body)
            if content_payload is not None:
                chat_mode = extract_native_result_mode(content_payload)
        chat_ok = False
        if (
            chat_ready.status_code == 200
            and chat_body is not None
            and chat_mode
            in {
                "similarity",
                "detection_only",
                "embedding_only",
            }
        ):
            chat_ok = True
        elif chat_ready.status_code == 503 and chat_mode == "engine_not_ready":
            chat_ok = True
            notes.append("Chat completions returned engine_not_ready for the local environment.")
        else:
            service_status = "broken"
        _record_check(
            name="chat_auth",
            ok=chat_ok,
            status_code=chat_ready.status_code,
            detail=chat_mode or "invalid chat response",
            checks=checks,
        )
    except Exception as exc:  # noqa: BLE001
        service_status = "broken"
        _record_check(
            name="chat_auth",
            ok=False,
            status_code=None,
            detail=f"request_failed: {exc.__class__.__name__}",
            checks=checks,
        )

    try:
        with client.stream(
            "POST",
            "/v1/chat/completions",
            headers=_auth_headers(api_key),
            json={
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
            },
        ) as stream_response:
            stream_body = "".join(stream_response.iter_text())
            stream_mode = None
            if stream_response.status_code == 200:
                stream_mode = extract_stream_result_mode(stream_body)
            elif stream_response.status_code == 503:
                try:
                    stream_json = json.loads(stream_body)
                except json.JSONDecodeError:
                    stream_json = None
                if isinstance(stream_json, dict):
                    stream_mode = extract_native_result_mode(stream_json)
            stream_ok = False
            if stream_response.status_code == 200 and stream_mode in {
                "similarity",
                "detection_only",
                "embedding_only",
            }:
                stream_ok = True
            elif stream_response.status_code == 503 and stream_mode == "engine_not_ready":
                stream_ok = True
                notes.append("Streaming chat returned engine_not_ready for the local environment.")
            else:
                service_status = "broken"
            _record_check(
                name="chat_stream",
                ok=stream_ok,
                status_code=stream_response.status_code,
                detail=stream_mode or "invalid stream response",
                checks=checks,
            )
    except Exception as exc:  # noqa: BLE001
        service_status = "broken"
        _record_check(
            name="chat_stream",
            ok=False,
            status_code=None,
            detail=f"request_failed: {exc.__class__.__name__}",
            checks=checks,
        )

    try:
        demo_response = client.get("/demo")
        demo_ok = demo_response.status_code == 200 and _check_demo_page(demo_response.text)
        if not demo_ok:
            service_status = "broken"
        _record_check(
            name="demo",
            ok=demo_ok,
            status_code=demo_response.status_code,
            detail="expected demo page" if demo_ok else "invalid demo response",
            checks=checks,
        )
    except Exception as exc:  # noqa: BLE001
        service_status = "broken"
        _record_check(
            name="demo",
            ok=False,
            status_code=None,
            detail=f"request_failed: {exc.__class__.__name__}",
            checks=checks,
        )

    if check_diagnostics:
        try:
            diagnostics_response = client.get(
                "/v1/diagnostics/startup",
                headers=_auth_headers(api_key),
            )
            diagnostics_body = _safe_json(diagnostics_response)
            if diagnostics_response.status_code == 404:
                diagnostics = {
                    "available": False,
                    "status": "unavailable",
                }
                notes.append("Startup diagnostics endpoint is unavailable on this deployment.")
            else:
                diagnostics_summary = (
                    extract_startup_diagnostics_summary(diagnostics_body)
                    if diagnostics_body is not None
                    else None
                )
                diagnostics_ok = (
                    diagnostics_response.status_code == 200 and diagnostics_summary is not None
                )
                if diagnostics_ok:
                    diagnostics = {
                        "available": True,
                        **diagnostics_summary,
                    }
                else:
                    service_status = "broken"
                    diagnostics = {
                        "available": True,
                        "status": "invalid",
                    }
                _record_check(
                    name="startup_diagnostics",
                    ok=diagnostics_ok,
                    status_code=diagnostics_response.status_code,
                    detail=(
                        diagnostics_summary["status"]
                        if diagnostics_summary is not None
                        else "invalid_diagnostics_response"
                    ),
                    checks=checks,
                )
        except Exception as exc:  # noqa: BLE001
            service_status = "broken"
            _record_check(
                name="startup_diagnostics",
                ok=False,
                status_code=None,
                detail=f"request_failed: {exc.__class__.__name__}",
                checks=checks,
            )

    if service_status != "broken" and readiness_status == "ready":
        service_status = "ready"

    report = {
        "base_url": base_url.rstrip("/"),
        "generated_at": datetime.now(UTC).isoformat(),
        "readiness_status": readiness_status,
        "service_status": service_status,
        "checks": checks,
        "notes": notes,
    }
    if diagnostics is not None:
        report["diagnostics"] = diagnostics
    return report


def format_smoke_report(report: dict[str, Any]) -> str:
    lines = [
        f"service_status: {report['service_status']}",
        f"readiness_status: {report['readiness_status']}",
    ]
    diagnostics = report.get("diagnostics")
    if isinstance(diagnostics, dict):
        if diagnostics.get("available") is False:
            lines.append("diagnostics: unavailable")
        else:
            summary = diagnostics.get("summary", {})
            lines.append(
                "diagnostics: "
                f"{diagnostics.get('status')} "
                f"env={diagnostics.get('environment')} "
                f"errors={summary.get('errors')} "
                f"warnings={summary.get('warnings')}"
            )
    for name, check in report["checks"].items():
        status = "ok" if check["ok"] else "fail"
        lines.append(f"- {name}: {status} (HTTP {check['status_code']}) {check['detail']}")
    if report["notes"]:
        lines.append("notes:")
        lines.extend(f"  - {note}" for note in report["notes"])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    report: dict[str, Any]
    with httpx.Client(base_url=args.base_url, timeout=args.timeout) as client:
        report = run_smoke_checks(
            client,
            api_key=args.api_key,
            base_url=args.base_url,
            check_diagnostics=args.check_diagnostics,
        )

    if args.output is not None:
        write_json_report(args.output, report)

    print(format_smoke_report(report))
    return 0 if report["service_status"] != "broken" else 1


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
