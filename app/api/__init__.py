from app.api.health import router as health_router
from app.api.readiness import router as readiness_router

__all__ = ["health_router", "readiness_router"]
