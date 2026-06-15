from fastapi.responses import JSONResponse


class AuthenticationError(Exception):
    """Raised when a request does not present a valid API key."""


def authentication_error_response() -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={
            "error": {
                "message": "Invalid or missing API key.",
                "type": "authentication_error",
                "code": "invalid_api_key",
            }
        },
        headers={"WWW-Authenticate": "Bearer"},
    )
