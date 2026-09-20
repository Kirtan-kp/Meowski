from app.vectorstore.qdrant_store import QdrantVectorStore
from app.services.session_service import SessionService
from app.services.session_state_service import SessionStateService
from fastapi import Depends
from app.services.bm25_index_service import BM25IndexService
from app.db.databse import get_db
from app.services.retrieval_cache_service import RetrievalCacheService
from app.services.llm_quota_service import LLMQuotaService

def get_vector_store():
    return QdrantVectorStore(embedding_dimension = 384)

session_state_service = SessionStateService()
bm25_index_service = BM25IndexService()
retrieval_cache_service = RetrievalCacheService()
llm_quota_service = LLMQuotaService()

def get_session_state_service():
    return session_state_service

def get_bm25_index_service():
    return bm25_index_service

def get_retrieval_cache_service():
    return retrieval_cache_service

def get_session_service(db = Depends(get_db) , state_service = Depends(get_session_state_service)):
    return SessionService(db = db , state_service = state_service)

def get_llm_quota_service():
    return llm_quota_service