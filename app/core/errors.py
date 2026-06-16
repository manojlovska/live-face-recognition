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
