from fastapi import APIRouter, Depends, HTTPException, Request
from app.schemas.chat import ChatRequest,ChatResponse
from app.services.chat_service import ChatService
from app.llm.exceptions import LLMTimeoutError,LLMRateLimitError,LLMProviderError,LLMQuotaExceededError,LLMProviderDisabledError,LLMConcurrencyLimitError
from app.core.config import settings
from app.services.session_service import SessionError, SessionNotFoundError
from app.api.dependencies import get_chat_service, get_rate_limit_service

router = APIRouter()

@router.post("/chat", response_model = ChatResponse)
def chat(request : ChatRequest , http_request : Request , chat_service : ChatService = Depends(get_chat_service), rate_limits = Depends(get_rate_limit_service)):
    session_allowed = rate_limits.is_allowed(
        key=f"session:chat:{rate_limits.scoped_key(request.user_id, request.session_id)}",
        limit=settings.session_rate_limit_requests,
        window_seconds=settings.session_rate_limit_window_seconds,
    )
    if not session_allowed:
        raise HTTPException(status_code=429, detail="Session rate limit exceeded")

    try:
        http_request.state.session_id = request.session_id
        response = chat_service.generate_response(message = request.message , session_id = request.session_id , user_id = request.user_id , 
                                                  request_id = http_request.state.request_id)
    except SessionError as exc:
        # Unknown session -> 404; inactive/expired -> 410 Gone (client should start a new one)
        raise HTTPException(
            status_code=404 if isinstance(exc, SessionNotFoundError) else 410,
            detail=str(exc),
        ) from exc

    except LLMTimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail=str(exc),
        ) from exc

    except LLMRateLimitError as exc:
        raise HTTPException(
            status_code=429,
            detail=str(exc),
            headers={"Retry-After": "20"},  # the provider's per-minute allowance refills quickly
        ) from exc

    except LLMProviderError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
    
    except LLMQuotaExceededError as exc:
        retry_after = getattr(exc, "retry_after", None)
        raise HTTPException(
            status_code=429,
            detail=str(exc),
            headers={"Retry-After": str(retry_after)} if retry_after else None,  # lets the UI say when to come back
        ) from exc

    except LLMProviderDisabledError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    except LLMConcurrencyLimitError as exc:
        raise HTTPException(
            status_code=429,
            detail=str(exc),
        ) from exc
    return {
        "response" : response.answer,
        "sources": response.sources,
        "mode": response.mode
    }