from pydantic import BaseModel, Field
from app.schemas.retrieval import Source

class ChatRequest(BaseModel):
    message : str = Field(min_length = 1 , max_length = 2000)
    session_id : str = Field(min_length = 1 , max_length = 100)
    user_id : str = Field(min_length = 1 , max_length = 100)

class ChatResponse(BaseModel):
    response : str
    sources : list[Source]
    mode : str = "portfolio"