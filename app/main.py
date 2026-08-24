from fastapi import FastAPI
from app.api.routes.chat import router as chat_router
from app.core.config import settings
from app.schemas.health import HealthResponse

app = FastAPI(title="Cat RAG API",
    description="RAG-based cat assistant backend",
    version="0.1.0")

app.include_router(chat_router)

@app.get("/health", response_model= HealthResponse)
def health():
    return {
        "status" : "ok",
        "environment" : settings.app_env
    }
