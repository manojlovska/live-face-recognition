from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.security import require_api_key
from app.services.config_validation import build_startup_diagnostics

router = APIRouter(
    prefix="/v1",
    tags=["diagnostics"],
    dependencies=[Depends(require_api_key)],
)


@router.get("/diagnostics/startup")
async def startup_diagnostics(request: Request) -> dict[str, object]:
    diagnostics = getattr(request.app.state, "startup_diagnostics", None)
    if diagnostics is None:
        diagnostics = build_startup_diagnostics(
            request.app.state.settings,
            request.app.state.model_runtime.status(),
        )
        request.app.state.startup_diagnostics = diagnostics
    return diagnostics
