from uuid import uuid4
from qdrant_client import QdrantClient
from qdrant_client.models import Distance,PointStruct,VectorParams
from app.core.config import settings
from app.vectorstore.base import VectorStore

class QdrantVectorStore(VectorStore):

    def __init__(self , embedding_dimension : int):
        self.client = QdrantClient(url = settings.qdrant_url)
        self.collection_name = settings.qdrant_collection
        self._create_collection_if_not_exists(embedding_dimension)

    def _create_collection_if_not_exists(self , embedding_dimension : int):
        collections = self.client.get_collections()
        collection_names = [collection.name for collection in collections.collections]

        if self.collection_name not in collection_names:
            self.client.create_collection(       #qdrant function to create collection
                collection_name = self.collection_name , 
                vectors_config = VectorParams(size = embedding_dimension , distance = Distance.COSINE)
            )

    def add_chunks(self, chunks):
        points = []                

        for chunk in chunks:           #transforming chunks into points
            point = PointStruct(       #qdrant function for point structure
                id = str(uuid4()),
                vector = chunk["vector"],
                payload = {
                    "text": chunk["text"],
                    "user_id": chunk["user_id"],
                    "session_id": chunk["session_id"],
                    "document_id": chunk["document_id"],
                    "filename": chunk["filename"],
                    "chunk_index": chunk["chunk_index"]
                }
            )
            points.append(point)
        self.client.upsert(collection_name = self.collection_name , points = points)   #qdrant function to send all constructed points in a single batch

    def search(self, query_vector , top_k=5, filters=None):
        results = self.client.query_points(collection_name = self.collection_name , query = query_vector , limit = top_k , query_filter = filters)
        return results.points

    def delete_document(self, document_id : str):
        pass