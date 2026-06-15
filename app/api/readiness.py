from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/readyz", tags=["health"], status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
async def readyz(request: Request) -> JSONResponse:
    settings = request.app.state.settings
    model_runtime = request.app.state.model_runtime
    runtime_status = model_runtime.readiness_summary()
    ready = bool(getattr(model_runtime, "is_ready", lambda: False)())
    response_status = status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE
    response_body = {
        "status": "ready" if ready else "not_ready",
        "service": settings.app_name,
        "version": settings.app_version,
        "checks": {
            "api": "ok",
            "models": "loaded" if ready else runtime_status["models"],
            "gallery": "loaded" if ready else runtime_status["gallery"],
            "model_assets": runtime_status["assets"],
        },
    }
    if "gallery_details" in runtime_status:
        response_body["checks"]["gallery_details"] = runtime_status["gallery_details"]
    return JSONResponse(status_code=response_status, content=response_body)
