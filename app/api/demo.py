from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["demo"])

_STATIC_DIR = Path(__file__).resolve().parents[1] / "static"
_DEMO_HTML = _STATIC_DIR / "demo.html"


@router.get("/demo", include_in_schema=False)
async def demo_page() -> FileResponse:
    return FileResponse(_DEMO_HTML, media_type="text/html")
