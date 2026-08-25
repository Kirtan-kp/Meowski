from app.services.embedding_service import EmbeddingService
from app.vectorstore.qdrant_store import QdrantVectorStore

embedding_service = EmbeddingService()

vector_store = QdrantVectorStore(embedding_dimension=384)

query = "What AI projects did Kirtan work on?"

query_vector = embedding_service.embed_text(query)

results = vector_store.search(
    query_vector = query_vector,
    top_k = 3
)

for result in results:

    print("\nScore:", result.score)

    print(
        "Text:",
        result.payload["text"]
    )