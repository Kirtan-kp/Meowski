from langchain_huggingface import HuggingFaceEmbeddings
from app.core.config import settings

class EmbeddingService:

    def __init__(self):
        self.embedding = HuggingFaceEmbeddings(model_name = settings.embedding_model)

    def embed_text(self , text : str) -> list[float]:
        vector = self.embedding.embed_query(text)
        return vector

    def embed_documents(self , texts : list[str]) -> list[list[float]]:
        vectors = self.embedding.embed_documents(texts)
        return vectors