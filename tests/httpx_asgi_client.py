from __future__ import annotations

import anyio
import httpx


class _ASGITransport(httpx.BaseTransport):
    def __init__(self, app: object, base_url: str = "http://testserver") -> None:
        self._app = app
        self._base_url = base_url

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        async def _send() -> tuple[httpx.Response, bytes]:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=self._app),
                base_url=self._base_url,
            ) as client:
                response = await client.request(
                    request.method,
                    str(request.url),
                    headers=request.headers,
                    content=request.content,
                )
                body = await response.aread()
                return response, body

        response, body = anyio.run(_send)
        return httpx.Response(
            status_code=response.status_code,
            headers=response.headers,
            content=body,
            request=request,
            extensions=response.extensions,
        )

    def close(self) -> None:
        return None


def build_openai_http_client(app: object, *, base_url: str = "http://testserver") -> httpx.Client:
    return httpx.Client(transport=_ASGITransport(app, base_url=base_url), base_url=base_url)
