from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.services.rate_limit_service import RateLimitService

rate_limit_service = RateLimitService()

def _endpoint(path: str) -> str | None:
    if path.endswith("/chat"):
        return "chat"
    if path.endswith("/documents") and path.count("/") >= 2:
        return "upload"
    return None

async def rate_limit_middleware(request: Request, call_next):
    path = request.url.path

    if path.endswith("/health"):
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            body_size = int(content_length)
        except ValueError:
            return JSONResponse(status_code=400, content={"detail": "Invalid Content-Length"})
        max_body = (
            settings.max_upload_request_bytes
            if _endpoint(path) == "upload"
            else settings.max_request_body_bytes
        )
        if body_size > max_body:
            return JSONResponse(status_code=413, content={"detail": "Request body is too large"})
    endpoint = _endpoint(path)

    if endpoint == "chat":
        allowed = rate_limit_service.is_allowed(
            key=f"chat:{client_ip}",
            limit=settings.rate_limit_requests,
            window_seconds=settings.rate_limit_window_seconds,
        )
        if not allowed:
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})

    elif endpoint == "upload":
        allowed = rate_limit_service.is_allowed(
            key=f"upload:{client_ip}",
            limit=settings.upload_rate_limit_requests,
            window_seconds=settings.upload_rate_limit_window_seconds,
        )
        if not allowed:
            return JSONResponse(status_code=429, content={"detail": "Upload rate limit exceeded"})

    return await call_next(request)