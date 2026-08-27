from qdrant_client.models import Filter, FieldCondition, MatchValue
from app.vectorstore.qdrant_store import QdrantVectorStore
from app.retrieval.pipeline import create_retrieval_pipeline
from app.llm.providers.groq import GroqLLM

vector_store = QdrantVectorStore(embedding_dimension = 384)

user_filter = Filter(       
    must=[                  
        FieldCondition(     
            key = "metadata.user_id",
            match = MatchValue(value = "user_1")
        ),
        FieldCondition(
            key = "metadata.session_id",
            match = MatchValue(value ="session_1")
        )
    ]
)

llm = GroqLLM()

retrieval_pipeline = create_retrieval_pipeline(vector_store = vector_store , llm = llm.llm , k = 10 , top_n = 3 , search_type = "mmr" , filter = user_filter)

documents = retrieval_pipeline.invoke("What projects did Kirtan work on?")

for document in documents:
    print("\nCONTENT:")
    print(document.page_content)

    print("\nMETADATA:")
    print(document.metadata)