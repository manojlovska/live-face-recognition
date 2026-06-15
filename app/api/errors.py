from fastapi.responses import JSONResponse


class AuthenticationError(Exception):
    """Raised when a request does not present a valid API key."""


class EngineNotReadyError(Exception):
    """Raised when face-similarity inference has not been loaded yet."""


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


def engine_not_ready_error_response() -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "error": {
                "message": (
                    "Face similarity engine is not ready. Models and gallery are not loaded."
                ),
                "type": "service_unavailable",
                "code": "engine_not_ready",
            }
        },
    )
