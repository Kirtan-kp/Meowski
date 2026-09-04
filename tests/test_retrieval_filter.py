from qdrant_client.models import Filter, FieldCondition, MatchValue
from app.vectorstore.qdrant_store import QdrantVectorStore
from app.retrieval.vector_retriever import create_vector_retriever
import pytest

@pytest.fixture
def vector_store():
    return QdrantVectorStore(embedding_dimension = 384)

def create_user_filter(user_id, session_id):
    return Filter(       #filter is for filtering rules.
        must=[                  #must[condition]  if every condition satisfied retrieve it or else return nothing
            FieldCondition(     #which field we are checking         since filtering can be more complex we are given these class
                key = "metadata.user_id",
                match = MatchValue(value = user_id)
            ),
            FieldCondition(
                key = "metadata.session_id",
                match = MatchValue(value = session_id)
            )
        ]
    )

def test_same_session_retrieval(vector_store):

    user_filter = create_user_filter(user_id = "user_1" , session_id = "session_1")
    retriever = create_vector_retriever(vector_store = vector_store , k = 5 , search_type = "similarity" , filter = user_filter)
    documents = retriever.invoke("What projects did Kirtan work on?")

    for document in documents:
        assert document.metadata.get("user_id") == "user_1"
        assert document.metadata.get("session_id") == "session_1"

def test_cross_session_isolation(vector_store):

    user_filter = create_user_filter(user_id = "user_1" , session_id = "session_2")
    retriever = create_vector_retriever(vector_store = vector_store , k = 5 , search_type = "similarity" , filter = user_filter)
    documents = retriever.invoke("What projects did Kirtan work on?")

    for document in documents:
        assert document.metadata.get("user_id") == "user_1"
        assert document.metadata.get("session_id") == "session_2"

def test_cross_user_isolation(vector_store):

    user_filter = create_user_filter(user_id = "user_2" , session_id = "session_2")
    retriever = create_vector_retriever(vector_store = vector_store , k = 5 , search_type = "similarity" , filter = user_filter)
    documents = retriever.invoke("What projects did Kirtan work on?")

    for document in documents:
        assert document.metadata.get("user_id") == "user_2"
        assert document.metadata.get("session_id") == "session_2"