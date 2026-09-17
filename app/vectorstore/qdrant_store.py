from langchain_qdrant import QdrantVectorStore as LangChainQdrantStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance,VectorParams
from app.core.config import settings
from app.vectorstore.base import VectorStore
from app.services.embedding_service import EmbeddingService
from langchain_core.documents import Document
from qdrant_client.models import Distance,VectorParams,Filter,FieldCondition,MatchValue
from qdrant_client import models

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

    def get_documents(self , file_id : str):

        scroll_filter = Filter(
            must=[
                FieldCondition(
                    key = "metadata.file_id",
                    match = MatchValue(value = file_id)
                )
            ]
        )

        documents = []
        offset = None

        while True:

            points , offset = self.client.scroll(collection_name = self.collection_name , scroll_filter = scroll_filter,
                                                 limit = 100 , offset = offset , with_payload = True , with_vectors = False)

            for point in points:

                payload = point.payload or {}
                page_content = payload.get("page_content" , "")
                metadata = payload.get("metadata" , {})

                if page_content:
                    documents.append(Document(page_content = page_content , metadata = metadata))

            if offset is None:
                break

        return documents             

    def has_file(self , file_hash : str , scope : str = "portfolio"):

        scroll_filter = Filter(
            must=[
                FieldCondition(
                    key="metadata.file_hash",
                    match=MatchValue(value=file_hash)
                ),
                FieldCondition(
                    key="metadata.scope",
                    match=MatchValue(value=scope)
                )
            ]
        )

        points , _ = self.client.scroll(collection_name = self.collection_name , scroll_filter = scroll_filter,
            limit = 1 , with_payload = False , with_vectors = False)

        return len(points) > 0

    def similarity_search(self , query , k = 5 , **kwargs):

        return self.vector_store.similarity_search(query = query , k = k , **kwargs)

    def as_retriever(self , **kwargs):
        
        return self.vector_store.as_retriever(**kwargs)

    def delete(self , **kwargs):

        return self.vector_store.delete(**kwargs)

    def delete_by_file_id(self, file_id: str):
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="metadata.file_id",
                            match=models.MatchValue(value=file_id),
                        )
                    ]
                )
            ),
        )