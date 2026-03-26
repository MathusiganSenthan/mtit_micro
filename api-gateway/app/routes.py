import os

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request, Response

load_dotenv()

router = APIRouter()

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8002")
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8003")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://localhost:8004")
NOTIFICATION_SERVICE_URL = os.getenv(
    "NOTIFICATION_SERVICE_URL", "http://localhost:8005"
)
FEEDBACK_SERVICE_URL = os.getenv("FEEDBACK_SERVICE_URL", "http://localhost:8006")

# Longer paths first so `/notifications/me` resolves on downstream (gateway forwards full path).
SERVICE_MAP = {
    "/auth": AUTH_SERVICE_URL,
    "/users": USER_SERVICE_URL,
    "/products": PRODUCT_SERVICE_URL,
    "/orders": ORDER_SERVICE_URL,
    "/notifications": NOTIFICATION_SERVICE_URL,
    "/feedback": FEEDBACK_SERVICE_URL,
}

# Hop-by-hop headers must not be forwarded (RFC 9110).
_HOP_BY_HOP = frozenset(
    {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
    }
)


async def _proxy(request: Request, target_base: str) -> Response:
    """
    Forward the incoming request to the target service, preserving
    method, headers, body, and query params.
    """
    # Strip the first path segment (the prefix) and forward the rest
    path = request.url.path
    query = request.url.query
    url = f"{target_base}{path}"
    if query:
        url = f"{url}?{query}"

    body = await request.body()

    # Forward all headers except the host header
    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() != "host"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            upstream = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=body,
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail=f"Service unavailable: {target_base}",
            )

    out_headers = {
        k: v
        for k, v in upstream.headers.items()
        if k.lower() not in _HOP_BY_HOP
    }

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers=out_headers,
    )


def _make_route(prefix: str, base_url: str):
    """Register catch-all GET/POST/PUT/PATCH/DELETE routes for a prefix."""

    @router.api_route(
        f"{prefix}/{{path:path}}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        tags=[prefix.strip("/")],
        name=f"proxy_{prefix.strip('/')}",
    )
    async def proxy_route(request: Request, path: str):
        return await _proxy(request, base_url)


for _prefix, _url in SERVICE_MAP.items():
    _make_route(_prefix, _url)