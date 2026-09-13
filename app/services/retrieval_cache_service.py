from langchain_core.documents import Document
from app.services.cache_service import CacheService

class RetrievalCacheService:
    def __init__(self):
        self.cache = CacheService()

    def get(self, key: str):
        cached_documents = self.cache.get(key)

        if cached_documents is None:
            return None

        return [
            Document(
                page_content=document["page_content"],
                metadata=document["metadata"]
            )
            for document in cached_documents
        ]

    def set(
        self,
        key: str,
        documents: list[Document],
        ttl_seconds: int
    ):
        serializable_documents = [
            {
                "page_content": document.page_content,
                "metadata": document.metadata
            }
            for document in documents
        ]

        self.cache.set(
            key,
            serializable_documents,
            ttl_seconds
        )

    def delete(self, key: str):
        self.cache.delete(key)