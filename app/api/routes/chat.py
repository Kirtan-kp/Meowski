from fastapi import APIRouter, Depends
from app.schemas.chat import ChatRequest,ChatResponse
from app.services.chat_service import ChatService

router = APIRouter()
chat_service = ChatService()

def get_chat_service():
    return chat_service

@router.post("/chat", response_model = ChatResponse)
def chat(request : ChatRequest, chat_service : ChatService = Depends(get_chat_service)):
    response = chat_service.generate_response(message = request.message , session_id = request.session_id , user_id = request.user_id)
    return {
        "response" : response.answer
    }