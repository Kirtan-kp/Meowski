from fastapi import APIRouter,HTTPException
from app.core.config import settings
from app.schemas.health import HealthResponse
from app.api.dependencies import get_vector_store
from app.db.databse import SessionLocal
from sqlalchemy import text
import redis

router = APIRouter()

@router.get(
    "/health",
    response_model=HealthResponse,
)
def health():
    dependencies: dict[str, str] = {}

    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        dependencies["postgres"] = "ok"
    except Exception:
        dependencies["postgres"] = "error"

    try:
        redis.Redis.from_url(settings.redis_url).ping()
        dependencies["redis"] = "ok"
    except Exception:
        dependencies["redis"] = "error"

    try:
        get_vector_store().client.get_collections()
        dependencies["qdrant"] = "ok"
    except Exception:
        dependencies["qdrant"] = "error"

    dependencies["llm"] = "configured" if settings.is_provider_enabled(settings.llm_provider) else "disabled"
    healthy = all(value in {"ok", "configured"} for value in dependencies.values())

    payload = {
        "status": "ok" if healthy else "degraded",
        "environment": settings.app_env,
        "dependencies": dependencies,
    }

    if not healthy:
        raise HTTPException(status_code=503, detail=payload)
    return payload