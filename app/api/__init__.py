from app.api.face_similarity import router as face_similarity_router
from app.api.health import router as health_router
from app.api.models import router as models_router
from app.api.readiness import router as readiness_router

__all__ = [
    "face_similarity_router",
    "health_router",
    "models_router",
    "readiness_router",
]
