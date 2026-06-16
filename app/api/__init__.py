from app.api.chat_completions import router as chat_completions_router
from app.api.demo import router as demo_router
from app.api.diagnostics import router as diagnostics_router
from app.api.face_similarity import router as face_similarity_router
from app.api.health import router as health_router
from app.api.models import router as models_router
from app.api.readiness import router as readiness_router

__all__ = [
    "chat_completions_router",
    "diagnostics_router",
    "demo_router",
    "face_similarity_router",
    "health_router",
    "models_router",
    "readiness_router",
]
