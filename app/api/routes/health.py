from fastapi import APIRouter
from app.core.config import settings
from app.schemas.health import HealthResponse

router = APIRouter()

@router.get(
    "/health",
    response_model=HealthResponse,
)
def health():
    return {
        "status": "ok",
        "environment": settings.app_env,
    }