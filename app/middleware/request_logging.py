import logging
import time
from fastapi import Request
import uuid
from app.api.dependencies import get_observability_service

logger = logging.getLogger(__name__)  #basically gets file name

def _route_label(request : Request) -> str:
    # Use the route template ("/api/v1/session/{session_id}") so unknown or
    # parameterised paths cannot create unbounded metric keys in Redis.
    route = request.scope.get("route")
    return getattr(route, "path", None) or "unmatched"

async def request_logging_middleware(request : Request , call_next):

    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    start_time = time.perf_counter()
    observability = get_observability_service()

    try:
        response = await call_next(request)

        latency_ms = (
            time.perf_counter() - start_time
        ) * 1000

        observability.record_request(
            request_id=request_id,
            route=_route_label(request),
            method=request.method,
            status_code=response.status_code,
            latency_ms=latency_ms,
            session_id=getattr(
                request.state,
                "session_id",
                None,
            ),
        )

        logger.info(
            "request_id=%s route=%s method=%s status=%s latency_ms=%.2f",
            request_id,
            request.url.path,
            request.method,
            response.status_code,
            latency_ms
        )
        response.headers["X-Request-ID"] = request_id

        return response
    
    except Exception as exc:

        latency_ms = (
            time.perf_counter() - start_time
        ) * 1000

        error_category = type(exc).__name__

        observability.record_request(
            request_id=request_id,
            route=_route_label(request),
            method=request.method,
            status_code=500,
            latency_ms=latency_ms,
            session_id=getattr(
                request.state,
                "session_id",
                None,
            ),
            error_category=error_category,
        )

        logger.exception(
            "request_id=%s route=%s method=%s error_category=%s latency_ms=%.2f",
            request_id,
            request.url.path,
            request.method,
            error_category,
            latency_ms
        )

        raise