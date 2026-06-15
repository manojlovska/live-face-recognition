import base64

import pytest

from app.api.errors import ImageValidationError
from app.services.image_input import decode_data_url_image
from tests.image_helpers import make_image_data_url, supports_webp


def test_valid_jpeg_data_url_decodes() -> None:
    decoded = decode_data_url_image(make_image_data_url("JPEG", size=(2, 3)), 1024)

    assert decoded.mime_type == "image/jpeg"
    assert decoded.width == 2
    assert decoded.height == 3
    assert decoded.rgb_array.shape == (3, 2, 3)
    assert decoded.rgb_array.dtype.name == "uint8"


def test_valid_png_data_url_decodes() -> None:
    decoded = decode_data_url_image(make_image_data_url("PNG", size=(2, 3)), 1024)

    assert decoded.mime_type == "image/png"
    assert decoded.width == 2
    assert decoded.height == 3
    assert decoded.rgb_array.shape == (3, 2, 3)
    assert decoded.rgb_array.dtype.name == "uint8"


@pytest.mark.skipif(not supports_webp(), reason="WebP not supported by local Pillow build")
def test_valid_webp_data_url_decodes() -> None:
    decoded = decode_data_url_image(make_image_data_url("WEBP", size=(2, 3)), 1024)

    assert decoded.mime_type == "image/webp"
    assert decoded.width == 2
    assert decoded.height == 3
    assert decoded.rgb_array.shape == (3, 2, 3)


def test_malformed_data_url_is_rejected() -> None:
    with pytest.raises(ImageValidationError) as exc_info:
        decode_data_url_image("not-a-data-url", 1024)

    assert exc_info.value.code == "invalid_image_data_url"
    assert exc_info.value.status_code == 400


def test_unsupported_mime_type_is_rejected() -> None:
    payload = base64.b64encode(b"placeholder").decode("ascii")

    with pytest.raises(ImageValidationError) as exc_info:
        decode_data_url_image(f"data:image/gif;base64,{payload}", 1024)

    assert exc_info.value.code == "unsupported_image_type"
    assert exc_info.value.status_code == 415


def test_invalid_base64_is_rejected() -> None:
    with pytest.raises(ImageValidationError) as exc_info:
        decode_data_url_image("data:image/jpeg;base64,@@@", 1024)

    assert exc_info.value.code == "invalid_image_base64"
    assert exc_info.value.status_code == 400


def test_too_large_decoded_payload_is_rejected() -> None:
    payload = base64.b64encode(b"x" * 32).decode("ascii")

    with pytest.raises(ImageValidationError) as exc_info:
        decode_data_url_image(f"data:image/jpeg;base64,{payload}", 16)

    assert exc_info.value.code == "image_too_large"
    assert exc_info.value.status_code == 413


def test_non_image_bytes_with_image_mime_are_rejected() -> None:
    payload = base64.b64encode(b"not an image").decode("ascii")

    with pytest.raises(ImageValidationError) as exc_info:
        decode_data_url_image(f"data:image/png;base64,{payload}", 1024)

    assert exc_info.value.code == "invalid_image"
    assert exc_info.value.status_code == 400
