from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.api.errors import ChatCompletionsError
from app.security import require_api_key
from app.services.openai_chat_adapter import analyze_chat_completion_request

router = APIRouter(
    prefix="/v1",
    tags=["chat-completions"],
    dependencies=[Depends(require_api_key)],
)


@router.post("/chat/completions")
async def create_chat_completion(request: Request) -> dict[str, object]:
    try:
        payload = await request.json()
    except ValueError as exc:
        raise ChatCompletionsError(
            message="Request body must be valid JSON.",
            code="invalid_chat_message",
            status_code=400,
        ) from exc

    settings = request.app.state.settings
    engine = request.app.state.face_similarity_engine
    return analyze_chat_completion_request(
        payload,
        settings=settings,
        engine=engine,
    )
