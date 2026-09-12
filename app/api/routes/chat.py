from fastapi import APIRouter, Depends
from app.schemas.chat import ChatRequest,ChatResponse
from app.services.chat_service import ChatService
from app.api.dependencies import get_vector_store
from app.api.dependencies import get_vector_store,get_session_service

router = APIRouter()
def get_chat_service(vector_store = Depends(get_vector_store) , session_service = Depends(get_session_service)):
    return ChatService(vector_store , session_service)

@router.post("/chat", response_model = ChatResponse)
def chat(request : ChatRequest, chat_service : ChatService = Depends(get_chat_service)):
    response = chat_service.generate_response(message = request.message , session_id = request.session_id , user_id = request.user_id)
    return {
        "response" : response.answer,
        "sources": response.sources
    }