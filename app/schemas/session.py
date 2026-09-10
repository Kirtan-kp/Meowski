from datetime import datetime
from pydantic import BaseModel

class CreateSessionRequest(BaseModel):
    user_id : str

class SessionResponse(BaseModel):
    session_id : str
    user_id : str
    status : str
    created_at : datetime
    expires_at : datetime