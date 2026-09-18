import logging
import time
from fastapi import Request
import uuid

logger = logging.getLogger(__name__)  #basically gets file name

async def request_logging_middleware(request : Request , call_next):

    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    start_time = time.perf_counter()

    try:
        response = await call_next(request)

        process_time = time.perf_counter() - start_time

        logger.info(
            "%s %s completed in %.4fs with status %s",
            request.method,
            request.url.path,
            process_time,
            response.status_code,
        )
        response.headers["X-Request-ID"] = request_id

        return response
    except Exception:

        process_time = time.perf_counter() - start_time

        logger.exception(
            "request_id=%s %s %s failed after %.4fs",
            request_id,
            request.method,
            request.url.path,
            process_time,
        )

        raise