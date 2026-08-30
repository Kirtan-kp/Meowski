from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.schemas.chat import ChatRequest,ChatResponse
from app.services.chat_service import ChatService

router = APIRouter()

def get_chat_service():
    return ChatService()

@router.post("/chat", response_model=ChatResponse)
def chat(request : ChatRequest, chat_service : ChatService = Depends(get_chat_service) ):
    response = chat_service.generate_response(message = request.message , session_id = request.session_id)
    return {
        "response" : response.answer
    }