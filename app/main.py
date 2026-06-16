import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from app.api import (
    chat_completions_router,
    demo_router,
    diagnostics_router,
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
from app.services.config_validation import (
    build_startup_diagnostics,
    format_startup_failure_message,
    should_fail_startup,
)
from app.services.face_similarity import FaceSimilarityEngine
from app.services.model_runtime import ModelRuntime

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    model_runtime = ModelRuntime(settings)
    startup_diagnostics = build_startup_diagnostics(settings, model_runtime.status())

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        report = getattr(app.state, "startup_diagnostics", startup_diagnostics)
        logger.info(
            "Startup diagnostics: environment=%s status=%s errors=%s warnings=%s",
            report["environment"],
            report["status"],
            report["summary"]["errors"],
            report["summary"]["warnings"],
        )
        if should_fail_startup(report, settings):
            logger.error(
                "Startup validation failed: environment=%s errors=%s warnings=%s",
                report["environment"],
                report["summary"]["errors"],
                report["summary"]["warnings"],
            )
            raise RuntimeError(format_startup_failure_message(report))
        yield

    app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
    app.state.settings = settings
    app.state.model_runtime = model_runtime
    app.state.face_similarity_engine = FaceSimilarityEngine(app.state.model_runtime)
    app.state.startup_diagnostics = startup_diagnostics
    static_dir = Path(__file__).resolve().parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    app.include_router(health_router)
    app.include_router(readiness_router)
    app.include_router(demo_router)
    app.include_router(models_router)
    app.include_router(diagnostics_router)
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
