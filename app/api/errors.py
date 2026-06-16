from fastapi.responses import JSONResponse

from app.core.errors import (
    AuthenticationError,
    ChatCompletionsError,
    EngineNotReadyError,
    GalleryStateError,
    ImageValidationError,
)

__all__ = [
    "AuthenticationError",
    "ChatCompletionsError",
    "EngineNotReadyError",
    "GalleryStateError",
    "ImageValidationError",
    "authentication_error_response",
    "chat_completions_error_response",
    "engine_not_ready_error_response",
    "gallery_state_error_response",
    "image_validation_error_response",
]


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
