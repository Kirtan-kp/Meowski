"""Only let the website's own proxy talk to the API.

When PROXY_SECRET is set, every request except /health must carry a matching X-Proxy-Secret header.
That header is added by the website's Cloudflare Pages Function, so strangers who find the tunnel URL cannot call
the API directly and spend your LLM tokens. The real visitor IP arrives in X-Visitor-IP and replaces the client
address so per-IP rate limits see visitors, not Cloudflare. With PROXY_SECRET empty (local dev) nothing changes."""
import hmac

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.config import settings


async def proxy_guard_middleware(request: Request, call_next):
    secret = settings.proxy_secret
    request.state.client_ip = request.client.host if request.client else "unknown"

    if secret and not request.url.path.endswith("/health"):
        given = request.headers.get("x-proxy-secret", "")
        if not hmac.compare_digest(given.encode(), secret.encode()):
            return JSONResponse(status_code=403, content={"detail": "Forbidden"})
        visitor = request.headers.get("x-visitor-ip", "").strip()
        if visitor:
            request.state.client_ip = visitor[:64]

    return await call_next(request)
