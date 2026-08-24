import logging
import time
from fastapi import Request

logger = logging.getLogger(__name__)  #basically gets file name

async def request_logging_middleware(request : Request , call_next):
    start_time = time.perf_counter()

    response = await call_next(request)

    process_time = time.perf_counter() - start_time

    logger.info(
        "%s %s completed in %.4fs with status %s",
        request.method,
        request.url.path,
        process_time,
        response.status_code,
    )

    return response