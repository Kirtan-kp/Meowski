from fastapi import FastAPI
from app.api.routes.chat import router as chat_router
from app.api.routes.upload import router as upload_router
from app.core.config import settings
from app.schemas.health import HealthResponse
from app.core.logging import setup_logging
from app.middleware.request_logging import request_logging_middleware
from app.db.databse import init_db
from app.api.routes.session import router as session_router
from app.db import models

setup_logging()

app = FastAPI(title = "Cat RAG API",
    description = "RAG-based cat assistant backend",
    version = "0.1.0")

init_db()

app.middleware("http")(request_logging_middleware)

app.include_router(chat_router)
app.include_router(upload_router)
app.include_router(session_router)

@app.get("/health", response_model = HealthResponse)
def health():
    return {
        "status" : "ok",
        "environment" : settings.app_env
    }
