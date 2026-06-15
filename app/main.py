from fastapi import FastAPI

from app.api import health_router
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version)
    app.state.settings = settings
    app.include_router(health_router)
    return app


app = create_app()
