from fastapi import FastAPI
from app.api.routes.chat import router as chat_router
from app.api.routes.upload import router as upload_router
from app.core.config import settings
from app.schemas.health import HealthResponse
from app.core.logging import setup_logging
from app.middleware.request_logging import request_logging_middleware
from app.middleware.rate_limit import rate_limit_middleware
from app.db.databse import init_db, SessionLocal
from app.api.routes.session import router as session_router
from app.db import models
import asyncio
from contextlib import asynccontextmanager
from app.services.cleanup_worker import cleanup_worker
from app.services.cleanup_service import CleanupService
from app.api.dependencies import get_vector_store,get_session_state_service,get_bm25_index_service,get_retrieval_cache_service

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()

    cleanup_service = CleanupService(
        db=db,
        vector_store=get_vector_store(),
        state_service=get_session_state_service(),
        bm25_index_service=get_bm25_index_service(),
        retrieval_cache_service=get_retrieval_cache_service()
    )

    cleanup_task = asyncio.create_task(
        cleanup_worker(cleanup_service)
    )

    try:
        yield
    finally:
        cleanup_task.cancel()

        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass

        db.close()

app = FastAPI(title = "Cat RAG API",
    description = "RAG-based cat assistant backend",
    version = "0.1.0",
    lifespan = lifespan)

init_db()

app.middleware("http")(request_logging_middleware)
app.middleware("http")(rate_limit_middleware)

app.include_router(chat_router)
app.include_router(upload_router)
app.include_router(session_router)

@app.get("/health", response_model = HealthResponse)
def health():
    return {
        "status" : "ok",
        "environment" : settings.app_env
    }
