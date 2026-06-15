from fastapi.responses import JSONResponse


class AuthenticationError(Exception):
    """Raised when a request does not present a valid API key."""


class EngineNotReadyError(Exception):
    """Raised when face-similarity inference has not been loaded yet."""


class ChatCompletionsError(Exception):
    """Raised when an OpenAI-style chat request is invalid or unsupported."""

    def __init__(
        self,
        *,
        message: str,
        code: str,
        status_code: int,
        error_type: str = "invalid_request_error",
        param: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.error_type = error_type
        self.param = param


class GalleryStateError(Exception):
    """Raised when gallery state is inconsistent with a similarity query."""

    def __init__(
        self,
        *,
        message: str,
        code: str,
        status_code: int = 500,
        error_type: str = "invalid_gallery_state",
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.error_type = error_type


class ImageValidationError(Exception):
    """Raised when a submitted image data URL or payload is invalid."""

    def __init__(
        self,
        *,
        message: str,
        code: str,
        status_code: int,
        error_type: str = "invalid_request_error",
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.error_type = error_type


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


def gallery_state_error_response(exc: GalleryStateError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "type": exc.error_type,
                "code": exc.code,
            }
        },
    )


def image_validation_error_response(exc: ImageValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "type": exc.error_type,
                "code": exc.code,
            }
        },
    )


def chat_completions_error_response(exc: ChatCompletionsError) -> JSONResponse:
    error_body = {
        "message": exc.message,
        "type": exc.error_type,
        "code": exc.code,
    }
    if exc.param is not None:
        error_body["param"] = exc.param

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": error_body},
    )
