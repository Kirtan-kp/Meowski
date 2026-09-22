from datetime import datetime
from pydantic import BaseModel

class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    scope: str
    created_at: datetime
    expires_at: datetime