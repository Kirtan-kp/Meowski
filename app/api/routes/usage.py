from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_llm_quota_service
from app.schemas.usage import UsageResponse

router = APIRouter()


@router.get("/usage", response_model=UsageResponse)
def usage(
    user_id: str = Query(min_length=1, max_length=100),
    session_id: str = Query(min_length=1, max_length=100),
    quota=Depends(get_llm_quota_service),
):
    """How much this visitor can still ask, so the UI can show an energy meter instead of surprising them with a 429."""
    return quota.get_usage(user_id=user_id, session_id=session_id)
