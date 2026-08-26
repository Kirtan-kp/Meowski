from qdrant_client.models import Filter, FieldCondition, MatchValue
from app.vectorstore.qdrant_store import QdrantVectorStore
from app.retrieval.vector_retriever import create_vector_retriever

vector_store = QdrantVectorStore(embedding_dimension = 384)

user_filter = Filter(       #filter is for filtering rules.
    must=[                  #must[condition]  if every condition satisfied retrieve it or else return nothing
        FieldCondition(     #which field we are checking         since filtering can be more complex we are given these class
            key = "metadata.user_id",
            match = MatchValue(value = "user_1")
        ),
        FieldCondition(
            key = "metadata.session_id",
            match = MatchValue(value ="session_9")
        )
    ]
)

retriever = create_vector_retriever(vector_store = vector_store , k = 5 , search_type = "similarity" , filter = user_filter)

documents = retriever.invoke("What projects did Kirtan work on?")

for document in documents:
    print("\nCONTENT:")
    print(document.page_content)

    print("\nMETADATA:")
    print(document.metadata)