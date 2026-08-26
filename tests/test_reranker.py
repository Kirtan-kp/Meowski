from app.retrieval.vector_retriever import create_vector_retriever
from app.retrieval.reranker import create_reranker
from app.vectorstore.qdrant_store import QdrantVectorStore

vector_store = QdrantVectorStore(embedding_dimension = 384)

retriever = create_vector_retriever(vector_store , k = 10)

reranker = create_reranker(retriever , top_n = 3)

documents = reranker.invoke("What projects did Kirtan work on?")

for document in documents:
    print("\nCONTENT:")
    print(document.page_content)

    print("\nMETADATA:")
    print(document.metadata)