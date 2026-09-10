from app.vectorstore.qdrant_store import QdrantVectorStore
from app.services.session_service import SessionService
from app.services.session_state_service import SessionStateService
from fastapi import Depends

from app.db.databse import get_db

vector_store = QdrantVectorStore(embedding_dimension = 384)

def get_vector_store():
    return vector_store

session_state_service = SessionStateService()

def get_session_state_service():
    return session_state_service

def get_session_service(db = Depends(get_db) , state_service = Depends(get_session_state_service)):
    return SessionService(db = db , state_service = state_service)