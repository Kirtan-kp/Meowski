from app.vectorstore.qdrant_store import QdrantVectorStore

vector_store = QdrantVectorStore(embedding_dimension = 384)

def get_vector_store():
    return vector_store