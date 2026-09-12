from qdrant_client.models import Filter, FieldCondition, MatchValue
from app.vectorstore.qdrant_store import QdrantVectorStore
from app.retrieval.vector_retriever import create_vector_retriever
import pytest

@pytest.fixture
def vector_store():
    
    vector_store = QdrantVectorStore(embedding_dimension = 384)
    vector_store.client.delete_collection(collection_name = vector_store.collection_name)
    vector_store._create_collection_if_not_exists(embedding_dimension = 384)

    return vector_store

def create_access_filter(user_id , session_id):
    return Filter(
        should=[
            Filter(
                must=[
                    FieldCondition(
                        key="metadata.scope",
                        match=MatchValue(value="portfolio")
                    )
                ]
            ),
            Filter(
                must=[
                    FieldCondition(
                        key="metadata.scope",
                        match=MatchValue(value="session")
                    ),
                    FieldCondition(
                        key="metadata.user_id",
                        match=MatchValue(value=user_id)
                    ),
                    FieldCondition(
                        key="metadata.session_id",
                        match=MatchValue(value=session_id)
                    )
                ]
            )
        ]
    )

def create_user_filter(user_id , session_id):
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

def test_access_filter_allows_portfolio_and_current_session(vector_store):

    from langchain_core.documents import Document

    vector_store.add_documents([
        Document(
            page_content="Portfolio project: Meowski RAG chatbot.",
            metadata={
                "scope": "portfolio"
            }
        ),
        Document(
            page_content="Session project: temporary cat assignment.",
            metadata={
                "scope": "session",
                "user_id": "user_1",
                "session_id": "session_1"
            }
        ),
        Document(
            page_content="Other session secret project.",
            metadata={
                "scope": "session",
                "user_id": "user_1",
                "session_id": "session_2"
            }
        ),
        Document(
            page_content="Other user private project.",
            metadata={
                "scope": "session",
                "user_id": "user_2",
                "session_id": "session_1"
            }
        )
    ])

    access_filter = create_access_filter(
        user_id="user_1",
        session_id="session_1"
    )

    retriever = create_vector_retriever(
        vector_store=vector_store,
        k=10,
        search_type="similarity",
        filter=access_filter
    )

    documents = retriever.invoke("project")

    contents = [
        document.page_content
        for document in documents
    ]

    assert "Portfolio project: Meowski RAG chatbot." in contents
    assert "Session project: temporary cat assignment." in contents
    assert "Other session secret project." not in contents
    assert "Other user private project." not in contents