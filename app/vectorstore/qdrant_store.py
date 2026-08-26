from langchain_qdrant import QdrantVectorStore as LangChainQdrantStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance,VectorParams
from app.core.config import settings
from app.vectorstore.base import VectorStore
from app.services.embedding_service import EmbeddingService

class QdrantVectorStore(VectorStore):

    def __init__(self , embedding_dimension : int):

        self.client = QdrantClient(url = settings.qdrant_url)
        self.collection_name = settings.qdrant_collection
        self._create_collection_if_not_exists(embedding_dimension)
        self.embedding_service = EmbeddingService()
        self.vector_store = LangChainQdrantStore(client = self.client , collection_name = self.collection_name , embedding = self.embedding_service.embedding)

    def _create_collection_if_not_exists(self , embedding_dimension : int):

        collections = self.client.get_collections()
        collection_names = [collection.name for collection in collections.collections]

        if self.collection_name not in collection_names:
            self.client.create_collection(       #qdrant function to create collection
                collection_name = self.collection_name , 
                vectors_config = VectorParams(size = embedding_dimension , distance = Distance.COSINE)
            )

    def add_documents(self, documents):

        return self.vector_store.add_documents(documents)                

    def similarity_search(self, query , k=5, **kwargs):

        return self.vector_store.similarity_search(query = query , k = k , **kwargs)

    def delete(self, **kwargs):

        return self.vector_store.delete(**kwargs)