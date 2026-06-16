from __future__ import annotations

import base64
import io
import json
import mimetypes
import statistics
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from PIL import Image

_IMAGE_MIME_TYPES = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}


def make_tiny_image_data_url(
    image_format: str = "JPEG",
    *,
    size: tuple[int, int] = (1, 1),
    color: tuple[int, int, int] = (255, 0, 0),
) -> str:
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, format=image_format)
    payload = base64.b64encode(buffer.getvalue()).decode("ascii")
    mime_type = _IMAGE_MIME_TYPES[image_format.upper()]
    return f"data:{mime_type};base64,{payload}"


def make_image_data_url_from_file(image_path: str | Path) -> str:
    path = Path(image_path)
    raw_bytes = path.read_bytes()
    mime_type, _ = mimetypes.guess_type(path.name)
    if mime_type is None:
        with Image.open(io.BytesIO(raw_bytes)) as image:
            format_name = (image.format or "JPEG").upper()
        mime_type = _IMAGE_MIME_TYPES.get(format_name, "image/jpeg")
    payload = base64.b64encode(raw_bytes).decode("ascii")
    return f"data:{mime_type};base64,{payload}"


def percentile(values: Iterable[float], p: float) -> float | None:
    ordered = sorted(values)
    if not ordered:
        return None
    if len(ordered) == 1:
        return float(ordered[0])

    rank = (len(ordered) - 1) * (p / 100.0)
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    if lower == upper:
        return float(ordered[lower])

    lower_value = ordered[lower]
    upper_value = ordered[upper]
    return float(lower_value + (upper_value - lower_value) * (rank - lower))


def summarize_latencies(values: Iterable[float]) -> dict[str, float | None]:
    samples = [float(value) for value in values]
    if not samples:
        return {"min": None, "mean": None, "median": None, "p95": None, "max": None}

    return {
        "min": min(samples),
        "mean": statistics.fmean(samples),
        "median": statistics.median(samples),
        "p95": percentile(samples, 95),
        "max": max(samples),
    }


def count_values(values: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def parse_sse_events(body: str) -> list[str]:
    events: list[str] = []
    current: list[str] = []

    for line in body.splitlines():
        if line.startswith("data:"):
            current.append(line.removeprefix("data:").lstrip())
            continue

        if not line.strip() and current:
            events.append("\n".join(current))
            current = []

    if current:
        events.append("\n".join(current))

    return events


def extract_native_result_mode(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None

    error = payload.get("error")
    if isinstance(error, dict) and error.get("code") == "engine_not_ready":
        return "engine_not_ready"

    mode = payload.get("mode")
    if isinstance(mode, str) and mode:
        return mode

    return None


def extract_chat_completion_content(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None

    if payload.get("object") != "chat.completion":
        error = payload.get("error")
        if isinstance(error, dict) and error.get("code") == "engine_not_ready":
            return {"mode": "engine_not_ready"}
        return None

    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return None

    choice = choices[0]
    if not isinstance(choice, dict):
        return None

    message = choice.get("message")
    if not isinstance(message, dict):
        return None

    content = message.get("content")
    if not isinstance(content, str):
        return None

    try:
        content_payload = json.loads(content)
    except json.JSONDecodeError:
        return None

    if isinstance(content_payload, dict):
        return content_payload
    return None


def extract_stream_result_mode(body: str) -> str | None:
    for event in parse_sse_events(body):
        if event == "[DONE]":
            continue

        try:
            chunk = json.loads(event)
        except json.JSONDecodeError:
            continue

        choices = chunk.get("choices")
        if not isinstance(choices, list):
            continue

        for choice in choices:
            if not isinstance(choice, dict):
                continue

            delta = choice.get("delta")
            if not isinstance(delta, dict):
                continue

            content = delta.get("content")
            if not isinstance(content, str):
                continue

            try:
                content_payload = json.loads(content)
            except json.JSONDecodeError:
                continue

            mode = extract_native_result_mode(content_payload)
            if mode:
                return mode

    return None


def write_json_report(path: str | Path, payload: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
