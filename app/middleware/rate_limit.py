from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.services.rate_limit_service import RateLimitService

rate_limit_service = RateLimitService()

async def rate_limit_middleware(request : Request , call_next):

    if request.url.path == "/health":
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"

    if request.url.path == "/chat":
        allowed = rate_limit_service.is_allowed(key = f"chat:{client_ip}" , limit = settings.rate_limit_requests,
                                                window_seconds = settings.rate_limit_window_seconds)

        if not allowed:
            return JSONResponse(status_code = 429 , content = {"detail": "Rate limit exceeded"})

    elif request.url.path == "/upload":
        allowed = rate_limit_service.is_allowed(key = f"upload:{client_ip}" , limit = settings.upload_rate_limit_requests,
            window_seconds = settings.upload_rate_limit_window_seconds)

        if not allowed:
            return JSONResponse(status_code = 429 , content = {"detail": "Upload rate limit exceeded"})

    return await call_next(request)