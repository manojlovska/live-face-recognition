from fastapi import APIRouter, Request, status

router = APIRouter()


@router.get("/readyz", tags=["health"], status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
async def readyz(request: Request) -> dict[str, object]:
    settings = request.app.state.settings
    model_runtime = request.app.state.model_runtime
    runtime_status = model_runtime.readiness_summary()
    return {
        "status": "not_ready",
        "service": settings.app_name,
        "version": settings.app_version,
        "checks": {
            "api": "ok",
            "models": runtime_status["models"],
            "gallery": runtime_status["gallery"],
            "model_assets": runtime_status["assets"],
        },
    }
