from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.vectorstore.qdrant_store import QdrantVectorStore
from app.retrieval.pipeline import create_retrieval_pipeline
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

retriever = create_retrieval_pipeline(
    vector_store=vector_store,
    llm=llm.llm,
    k=20,
    top_n=3,
    search_type="mmr",
    filter=user_filter
)

retriever = retriever.retriever

questions = [
    "What projects has Kirtan worked on?",
    "What technologies has Kirtan worked with?"
]


for question in questions:
    print("\n" + "=" * 80)
    print("QUESTION:", question)
    print("=" * 80)

    documents = retriever.invoke(question)

    for rank, document in enumerate(documents, start=1):
        print(f"\n--- RANK {rank} ---")
        print("CHUNK:", document.metadata.get("chunk_index"))
        print("SOURCE:", document.metadata.get("source"))
        print("CONTENT:")
        print(document.page_content)