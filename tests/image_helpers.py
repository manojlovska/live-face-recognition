from __future__ import annotations

import base64
import io

from PIL import Image, features

_MIME_TYPES = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}


def make_image_data_url(
    image_format: str,
    *,
    size: tuple[int, int] = (1, 1),
    color: tuple[int, int, int] = (255, 0, 0),
) -> str:
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, format=image_format)
    mime_type = _MIME_TYPES[image_format.upper()]
    payload = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:{mime_type};base64,{payload}"


def supports_webp() -> bool:
    return bool(features.check("webp"))
