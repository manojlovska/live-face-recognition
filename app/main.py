from fastapi import FastAPI, Request

from app.api import (
    chat_completions_router,
    face_similarity_router,
    health_router,
    models_router,
    readiness_router,
)
from app.api.errors import (
    AuthenticationError,
    ChatCompletionsError,
    EngineNotReadyError,
    GalleryStateError,
    ImageValidationError,
    authentication_error_response,
    chat_completions_error_response,
    engine_not_ready_error_response,
    gallery_state_error_response,
    image_validation_error_response,
)
from app.config import get_settings
from app.services.face_similarity import FaceSimilarityEngine
from app.services.model_runtime import ModelRuntime


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version)
    app.state.settings = settings
    app.state.model_runtime = ModelRuntime(settings)
    app.state.face_similarity_engine = FaceSimilarityEngine(app.state.model_runtime)
    app.include_router(health_router)
    app.include_router(readiness_router)
    app.include_router(models_router)
    app.include_router(face_similarity_router)
    app.include_router(chat_completions_router)
    app.add_exception_handler(AuthenticationError, auth_error_handler)
    app.add_exception_handler(ChatCompletionsError, chat_completions_error_handler)
    app.add_exception_handler(EngineNotReadyError, engine_not_ready_handler)
    app.add_exception_handler(GalleryStateError, gallery_state_handler)
    app.add_exception_handler(ImageValidationError, image_validation_handler)
    return app


async def auth_error_handler(_request: Request, _exc: AuthenticationError):
    return authentication_error_response()


async def chat_completions_error_handler(_request: Request, exc: ChatCompletionsError):
    return chat_completions_error_response(exc)


async def engine_not_ready_handler(_request: Request, _exc: EngineNotReadyError):
    return engine_not_ready_error_response()


async def gallery_state_handler(_request: Request, exc: GalleryStateError):
    return gallery_state_error_response(exc)


async def image_validation_handler(_request: Request, exc: ImageValidationError):
    return image_validation_error_response(exc)


app = create_app()
