from fastapi import APIRouter, Depends, Header, HTTPException
from app.api.dependencies import get_observability_service
from app.services.observability_service import ObservabilityService
from app.core.config import settings

router = APIRouter()

@router.get("/metrics")
def metrics(
    x_metrics_token: str | None = Header(default=None),
    observability: ObservabilityService = Depends(get_observability_service),
):
    if settings.metrics_token and x_metrics_token != settings.metrics_token:
        raise HTTPException(status_code=401, detail="Metrics access denied")
    if settings.app_env.lower() == "production" and not settings.metrics_token:
        raise HTTPException(status_code=503, detail="Metrics access is not configured")
    return observability.get_metrics()