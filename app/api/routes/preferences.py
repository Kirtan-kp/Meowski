from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_preference_service
from app.schemas.preferences import (
    CreatePreferenceRequest,
    PreferenceResponse,
)
from app.services.preference_service import PreferenceService


router = APIRouter()


@router.post(
    "/preferences",
    response_model=PreferenceResponse,
)
def save_preference(
    request: CreatePreferenceRequest,
    preference_service: PreferenceService = Depends(
        get_preference_service
    ),
):

    preference = preference_service.save_preference(
        user_id=request.user_id,
        key=request.key,
        value=request.value,
    )

    return preference


@router.delete(
    "/preferences/{preference_id}",
)
def delete_preference(
    preference_id: str,
    user_id: str,
    preference_service: PreferenceService = Depends(
        get_preference_service
    ),
):

    deleted = preference_service.delete_preference(
        preference_id=preference_id,
        user_id=user_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Preference not found",
        )

    return {
        "message": "Preference deleted successfully"
    }