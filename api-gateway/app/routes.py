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


async def _proxy(
    request: Request,
    target_base: str,
    forward_path: str | None = None,
) -> Response:
    """
    Forward the incoming request to the target service, preserving
    method, headers, body, and query params.
    """
    # Strip the first path segment (the prefix) and forward the rest
    path = forward_path if forward_path is not None else request.url.path
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
    """Register proxy routes for a service prefix (including root path)."""

    @router.get(
        f"{prefix}/docs",
        tags=[prefix.strip("/")],
        name=f"proxy_docs_{prefix.strip('/')}",
    )
    async def proxy_docs(request: Request):
        return await _proxy(request, base_url, "/docs")

    @router.get(
        f"{prefix}/openapi.json",
        tags=[prefix.strip("/")],
        name=f"proxy_openapi_{prefix.strip('/')}",
    )
    async def proxy_openapi(request: Request):
        return await _proxy(request, base_url, "/openapi.json")

    @router.get(
        f"{prefix}/redoc",
        tags=[prefix.strip("/")],
        name=f"proxy_redoc_{prefix.strip('/')}",
    )
    async def proxy_redoc(request: Request):
        return await _proxy(request, base_url, "/redoc")

    @router.api_route(
        f"{prefix}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
        tags=[prefix.strip("/")],
        name=f"proxy_root_{prefix.strip('/')}",
    )
    @router.api_route(
        f"{prefix}/",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
        tags=[prefix.strip("/")],
        name=f"proxy_root_slash_{prefix.strip('/')}",
    )
    async def proxy_root(request: Request):
        return await _proxy(request, base_url)

    @router.api_route(
        f"{prefix}/{{path:path}}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
        tags=[prefix.strip("/")],
        name=f"proxy_{prefix.strip('/')}",
    )
    async def proxy_route(request: Request, path: str):
        return await _proxy(request, base_url)


for _prefix, _url in SERVICE_MAP.items():
    _make_route(_prefix, _url)


@router.get("/gateway/services", tags=["gateway"])
async def list_services():
    return {
        "services": [
            {"prefix": prefix, "url": url} for prefix, url in SERVICE_MAP.items()
        ]
    }


@router.get("/gateway/health", tags=["gateway"])
async def gateway_health():
    statuses = []
    async with httpx.AsyncClient(timeout=5.0) as client:
        for prefix, url in SERVICE_MAP.items():
            health_url = f"{url}/health"
            try:
                r = await client.get(health_url)
                statuses.append(
                    {
                        "service": prefix,
                        "url": url,
                        "status_code": r.status_code,
                        "healthy": r.status_code < 400,
                    }
                )
            except httpx.HTTPError:
                statuses.append(
                    {
                        "service": prefix,
                        "url": url,
                        "status_code": None,
                        "healthy": False,
                    }
                )

    all_healthy = all(item["healthy"] for item in statuses)
    return {"healthy": all_healthy, "services": statuses}


@router.get("/gateway/docs", tags=["gateway"])
async def docs_index():
    docs = []
    for prefix, url in SERVICE_MAP.items():
        docs.append(
            {
                "service": prefix.strip("/"),
                "direct_docs": f"{url}/docs",
                "gateway_docs": f"{prefix}/docs",
                "gateway_openapi": f"{prefix}/openapi.json",
            }
        )
    return {"docs": docs}