from fastapi import FastAPI, Request

from app.api import face_similarity_router, health_router, models_router, readiness_router
from app.api.errors import (
    AuthenticationError,
    EngineNotReadyError,
    authentication_error_response,
    engine_not_ready_error_response,
)
from app.config import get_settings
from app.services.face_similarity import FaceSimilarityEngine


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version)
    app.state.settings = settings
    app.state.face_similarity_engine = FaceSimilarityEngine()
    app.include_router(health_router)
    app.include_router(readiness_router)
    app.include_router(models_router)
    app.include_router(face_similarity_router)
    app.add_exception_handler(AuthenticationError, auth_error_handler)
    app.add_exception_handler(EngineNotReadyError, engine_not_ready_handler)
    return app


async def auth_error_handler(_request: Request, _exc: AuthenticationError):
    return authentication_error_response()


async def engine_not_ready_handler(_request: Request, _exc: EngineNotReadyError):
    return engine_not_ready_error_response()


app = create_app()
