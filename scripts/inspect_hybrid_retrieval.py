from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.vectorstore.qdrant_store import QdrantVectorStore
from app.retrieval.vector_retriever import create_vector_retriever
from app.retrieval.bm25_retriever import create_bm25_retriever
from app.retrieval.pipeline import RuntimeFilteredEnsembleRetriever
from app.llm.providers.groq import GroqLLM


vector_store = QdrantVectorStore(embedding_dimension=384)

user_filter = Filter(
    must=[
        FieldCondition(
            key="metadata.scope",
            match=MatchValue(value="portfolio")
        )
    ]
)

llm = GroqLLM()

vector_retriever = create_vector_retriever(
    vector_store=vector_store,
    k=20,
    search_type="mmr",
    search_kwargs=None
)

bm25_retriever = create_bm25_retriever(
    vector_store=vector_store,
    filter=user_filter,
    k=20
)

hybrid_retriever = RuntimeFilteredEnsembleRetriever(
    vector_retriever=vector_retriever,
    bm25_retriever=bm25_retriever,
    weights=[0.5, 0.5],
    candidate_limit=30,
    default_filter=user_filter
)


questions = [
    "What projects has Kirtan worked on?",
    "What technologies has Kirtan worked with?"
]


for question in questions:

    print("\n" + "=" * 100)
    print("QUESTION:", question)
    print("=" * 100)

    vector_documents = vector_retriever.invoke(
        question,
        filter=user_filter
    )

    print("\n========== DENSE RETRIEVAL ==========")

    for rank, document in enumerate(vector_documents, start=1):
        print(
            f"{rank}. CHUNK "
            f"{document.metadata.get('chunk_index')}"
        )

    bm25_documents = bm25_retriever._get_relevant_documents(
        question,
        run_manager=None,
        filter=user_filter
    )

    print("\n========== BM25 RETRIEVAL ==========")

    for rank, document in enumerate(bm25_documents, start=1):
        print(
            f"{rank}. CHUNK "
            f"{document.metadata.get('chunk_index')}"
        )

    hybrid_documents = hybrid_retriever.invoke(question)

    print("\n========== HYBRID / RRF ==========")

    for rank, document in enumerate(hybrid_documents, start=1):
        print(
            f"{rank}. CHUNK "
            f"{document.metadata.get('chunk_index')}"
        )

    print()