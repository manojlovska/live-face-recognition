from __future__ import annotations

import base64
import binascii
import io
from dataclasses import dataclass
from typing import Final

import numpy as np
from PIL import Image, UnidentifiedImageError

from app.core.errors import ImageValidationError

ALLOWED_IMAGE_MIME_TYPES: Final = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

_BASE64_PREFIX = "data:"


@dataclass(slots=True)
class DecodedImage:
    mime_type: str
    width: int
    height: int
    rgb_array: np.ndarray


def decode_data_url_image(data_url: str, max_image_bytes: int) -> DecodedImage:
    if not isinstance(data_url, str) or not data_url.startswith(_BASE64_PREFIX):
        raise ImageValidationError(
            message="Image must be provided as a base64 data URL.",
            code="invalid_image_data_url",
            status_code=400,
        )

    header, separator, payload = data_url.partition(",")
    if separator != ",":
        raise ImageValidationError(
            message="Image must be provided as a base64 data URL.",
            code="invalid_image_data_url",
            status_code=400,
        )

    mime_type = _parse_mime_type(header)
    if mime_type not in ALLOWED_IMAGE_MIME_TYPES:
        raise ImageValidationError(
            message="Unsupported image type.",
            code="unsupported_image_type",
            status_code=415,
            error_type="unsupported_media_type",
        )

    if _estimate_decoded_size(payload) > max_image_bytes:
        raise ImageValidationError(
            message="Decoded image is too large.",
            code="image_too_large",
            status_code=413,
            error_type="request_too_large",
        )

    try:
        decoded_bytes = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ImageValidationError(
            message="Image base64 payload is invalid.",
            code="invalid_image_base64",
            status_code=400,
        ) from exc

    if len(decoded_bytes) > max_image_bytes:
        raise ImageValidationError(
            message="Decoded image is too large.",
            code="image_too_large",
            status_code=413,
            error_type="request_too_large",
        )

    try:
        with Image.open(io.BytesIO(decoded_bytes)) as image:
            image.load()
            rgb_image = image.convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ImageValidationError(
            message="The provided image could not be decoded.",
            code="invalid_image",
            status_code=400,
        ) from exc

    rgb_array = np.array(rgb_image, dtype=np.uint8)
    width, height = rgb_image.size
    return DecodedImage(
        mime_type=mime_type,
        width=width,
        height=height,
        rgb_array=rgb_array,
    )


def _parse_mime_type(header: str) -> str:
    mime_section = header[len(_BASE64_PREFIX) :]
    parts = mime_section.split(";")
    if len(parts) != 2 or parts[1].lower() != "base64" or not parts[0]:
        raise ImageValidationError(
            message="Image must be provided as a base64 data URL.",
            code="invalid_image_data_url",
            status_code=400,
        )

    return parts[0].lower()


def _estimate_decoded_size(payload: str) -> int:
    if not payload:
        return 0

    return ((len(payload) + 3) // 4) * 3
