from fastapi import FastAPI, Request

from app.api import health_router, readiness_router
from app.api.errors import AuthenticationError, authentication_error_response
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version)
    app.state.settings = settings
    app.include_router(health_router)
    app.include_router(readiness_router)
    app.add_exception_handler(AuthenticationError, auth_error_handler)
    return app


async def auth_error_handler(_request: Request, _exc: AuthenticationError):
    return authentication_error_response()


app = create_app()
