from fastapi import APIRouter, Depends, HTTPException, Request
from app.schemas.chat import ChatRequest,ChatResponse
from app.services.chat_service import ChatService
from app.api.dependencies import get_vector_store,get_session_service,get_bm25_index_service
from app.llm.exceptions import LLMTimeoutError,LLMRateLimitError,LLMProviderError,LLMQuotaExceededError,LLMProviderDisabledError,LLMConcurrencyLimitError
from app.api.dependencies import get_preference_service, get_rate_limit_service
from app.core.config import settings

router = APIRouter()
def get_chat_service(vector_store = Depends(get_vector_store) , session_service = Depends(get_session_service) ,
                    bm25_index_service = Depends(get_bm25_index_service) , preference_service=Depends(get_preference_service)):
    return ChatService(vector_store , session_service , bm25_index_service , preference_service)

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
    except LLMTimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail=str(exc),
        ) from exc

    except LLMRateLimitError as exc:
        raise HTTPException(
            status_code=429,
            detail=str(exc),
        ) from exc

    except LLMProviderError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
    
    except LLMQuotaExceededError as exc:
        raise HTTPException(
            status_code=429,
            detail=str(exc),
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
        "sources": response.sources
    }