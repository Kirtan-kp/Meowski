from fastapi import APIRouter, Depends
from app.api.dependencies import get_observability_service
from app.services.observability_service import ObservabilityService

router = APIRouter()

@router.get("/metrics")
def metrics(
    observability: ObservabilityService = Depends(
        get_observability_service
    )
):
    return observability.get_metrics()