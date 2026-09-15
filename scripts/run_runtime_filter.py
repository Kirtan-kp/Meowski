from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.vectorstore.qdrant_store import QdrantVectorStore
from app.llm.providers.groq import GroqLLM
from app.retrieval.pipeline import create_retrieval_pipeline


vector_store = QdrantVectorStore(embedding_dimension=384)
llm = GroqLLM()

retriever = create_retrieval_pipeline(
    vector_store=vector_store,
    llm=llm.llm,
    k=10,
    top_n=3,
    search_type="mmr"
)

access_filter = Filter(
    must=[
        FieldCondition(
            key="metadata.user_id",
            match=MatchValue(value="user_1")
        ),
        FieldCondition(
            key="metadata.session_id",
            match=MatchValue(value="session_2")
        )
    ]
)

documents = retriever.invoke(
    "What projects did Kirtan work on?",
    filter=access_filter
)

print("\nRESULTS:")
print("-" * 60)

for document in documents:
    print(f"USER: {document.metadata.get('user_id')}")
    print(f"SESSION: {document.metadata.get('session_id')}")
    print(f"CONTENT: {document.page_content}")
    print("-" * 60)