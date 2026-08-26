from app.vectorstore.qdrant_store import QdrantVectorStore

vector_store = QdrantVectorStore(embedding_dimension=384)

query = "What AI projects did Kirtan work on?"

results = vector_store.similarity_search(
    query = query,
    k = 3
)

for result in results:
    print(result.page_content)
    print(result.metadata)