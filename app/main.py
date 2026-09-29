from fastapi import FastAPI
from app.api.routes.chat import router as chat_router
from app.api.routes.upload import router as upload_router
from app.core.logging import setup_logging
from app.middleware.request_logging import request_logging_middleware
from app.middleware.rate_limit import rate_limit_middleware
from app.db.databse import init_db
from app.api.routes.session import router as session_router
import asyncio
from contextlib import asynccontextmanager
from app.services.cleanup_worker import cleanup_worker
from app.api.routes.metrics import router as metrics_router
from app.api.routes.preferences import router as preferences_router
from app.api.routes.health import router as health_router

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    cleanup_task = asyncio.create_task(
        cleanup_worker()
    )

    try:
        yield
    finally:
        cleanup_task.cancel()

        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass

app = FastAPI(title = "Cat RAG API",
    description = "RAG-based cat assistant backend",
    version = "0.1.0",
    lifespan = lifespan)

init_db()

# Starlette runs the LAST-added middleware first (outermost). Rate limiting is added
# first so request logging/metrics also see the 429 responses it produces.
app.middleware("http")(rate_limit_middleware)
app.middleware("http")(request_logging_middleware)

API_PREFIX = "/api/v1"

app.include_router(chat_router , prefix=API_PREFIX)
app.include_router(upload_router , prefix=API_PREFIX)
app.include_router(session_router , prefix=API_PREFIX)
app.include_router(metrics_router , prefix=API_PREFIX)
app.include_router(preferences_router , prefix=API_PREFIX)
app.include_router(health_router , prefix=API_PREFIX)