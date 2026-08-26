from app.retrieval.vector_retriever import create_vector_retriever
from app.vectorstore.qdrant_store import QdrantVectorStore

vector_store = QdrantVectorStore(embedding_dimension = 384)

retriever = create_vector_retriever(vector_store = vector_store , k = 3)

query = "What AI projects did Kirtan work on?"

results = retriever.invoke(query)

for result in results:
    print("\nCONTENT:")
    print(result.page_content)

    print("\nMETADATA:")
    print(result.metadata)   #Keeping metadata for filetering later