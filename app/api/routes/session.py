from fastapi import APIRouter, Depends, HTTPException
from app.api.dependencies import get_session_service
from app.schemas.session import CreateSessionRequest,SessionResponse
from app.services.session_service import SessionService

router = APIRouter()

@router.post(
    "/session",
    response_model=SessionResponse
)
def create_session(request : CreateSessionRequest , session_service : SessionService = Depends(get_session_service)):
    session = session_service.create_session(user_id = request.user_id)

    return SessionResponse(session_id = session.id , user_id = session.user_id , status = session.status ,
                           created_at = session.created_at , expires_at = session.expires_at)

@router.get(
    "/session",
    response_model=SessionResponse,
)
def get_current_session(
    session_id: str,
    user_id: str,
    session_service: SessionService = Depends(
        get_session_service
    ),
):
    try:
        session = session_service.get_session(
            session_id=session_id,
            user_id=user_id,
        )

        return SessionResponse(
            session_id=session.id,
            user_id=session.user_id,
            status=session.status,
            created_at=session.created_at,
            expires_at=session.expires_at,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

@router.get(
    "/session/{session_id}",
    response_model=SessionResponse
)
def get_session(session_id : str , user_id : str , session_service : SessionService = Depends(get_session_service)):
    try:
        session = session_service.get_session(session_id = session_id , user_id = user_id)

        return SessionResponse(session_id = session.id , user_id = session.user_id , status = session.status ,
            created_at = session.created_at , expires_at = session.expires_at)

    except ValueError as exc:
        raise HTTPException(status_code = 404 , detail = str(exc))