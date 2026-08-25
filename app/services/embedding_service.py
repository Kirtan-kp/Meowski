from sentence_transformers import SentenceTransformer
from app.core.config import settings

class EmbeddingService:

    def __init__(self):
        self.model = SentenceTransformer(settings.embedding_model)

    def embed_text(self , text : str) -> list[float]:
        vector = self.model.encode(text , normalize_embeddings = True)
        return vector.tolist()

    def embed_documents(self , texts : list[str]) -> list[list[float]]:
        vectors = self.model.encode(texts , normalize_embeddings = True)
        return vectors.tolist()