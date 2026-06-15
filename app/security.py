import secrets

from fastapi import Header

from app.api.errors import AuthenticationError
from app.config import get_settings


def require_api_key(authorization: str | None = Header(default=None)) -> None:
    settings = get_settings()
    expected_key = (settings.face_api_key or "").strip()

    if not expected_key:
        raise AuthenticationError

    if not authorization:
        raise AuthenticationError

    parts = authorization.split()
    if len(parts) != 2:
        raise AuthenticationError

    scheme, provided_key = parts
    if scheme.lower() != "bearer":
        raise AuthenticationError

    if not provided_key or not secrets.compare_digest(expected_key, provided_key):
        raise AuthenticationError

    return None
