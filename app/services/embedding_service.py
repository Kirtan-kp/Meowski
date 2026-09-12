from langchain_huggingface import HuggingFaceEmbeddings
from app.core.config import settings
import hashlib
from app.services.cache_service import CacheService
from langchain_core.embeddings import Embeddings

class CachedEmbeddings(Embeddings):
    def __init__(self , embedding , cache):
        self.embedding = embedding
        self.cache = cache

    def _cache_key(self , text : str) -> str:

        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

        return f"cache:embedding:{settings.embedding_model}:{text_hash}"

    def embed_query(self , text : str) -> list[float]:

        key = self._cache_key(text)
        cached_embedding = self.cache.get(key)

        if cached_embedding is not None:
            return cached_embedding

        embedding = self.embedding.embed_query(text)
        self.cache.set(key , embedding , ttl_seconds = 86400)

        return embedding

    def embed_documents(self , texts : list[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]

class EmbeddingService:

    def __init__(self):

        embedding = HuggingFaceEmbeddings(model_name = settings.embedding_model)
        cache = CacheService()
        self.embedding = CachedEmbeddings(embedding = embedding , cache = cache)

    def embed_text(self , text : str) -> list[float]:
        return self.embedding.embed_query(text)

    def embed_documents(self , texts : list[str]) -> list[list[float]]:
        return self.embedding.embed_documents(texts)