from qdrant_client.models import Filter, FieldCondition, MatchValue
from app.vectorstore.qdrant_store import QdrantVectorStore
from app.retrieval.vector_retriever import create_vector_retriever
from app.retrieval.bm25_retriever import create_bm25_retriever
from app.services.bm25_index_service import BM25IndexService
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

def test_bm25_access_filter_allows_portfolio_and_current_session(vector_store):

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

    retriever = create_bm25_retriever(
        vector_store=vector_store,
        k=10,
        index_service=BM25IndexService()
    )

    documents = retriever.invoke(
        "project",
        filter=access_filter
    )

    contents = [
        document.page_content
        for document in documents
    ]

    assert "Portfolio project: Meowski RAG chatbot." in contents
    assert "Session project: temporary cat assignment." in contents
    assert "Other session secret project." not in contents
    assert "Other user private project." not in contents

def test_bm25_requires_access_filter(vector_store):

    from app.retrieval.bm25_retriever import create_bm25_retriever
    from app.services.bm25_index_service import BM25IndexService

    retriever = create_bm25_retriever(
        vector_store=vector_store,
        k=10,
        index_service=BM25IndexService()
    )

    with pytest.raises(ValueError, match="filter"):
        retriever.invoke("project")

def test_bm25_different_sessions_use_different_indexes(vector_store):

    from langchain_core.documents import Document

    vector_store.add_documents([
        Document(
            page_content="Session one private project.",
            metadata={
                "scope": "session",
                "user_id": "user_1",
                "session_id": "session_1"
            }
        ),
        Document(
            page_content="Session two private project.",
            metadata={
                "scope": "session",
                "user_id": "user_1",
                "session_id": "session_2"
            }
        )
    ])

    index_service = BM25IndexService()

    retriever = create_bm25_retriever(
        vector_store=vector_store,
        k=10,
        index_service=index_service
    )

    session_1_filter = Filter(
        must=[
            FieldCondition(
                key="metadata.scope",
                match=MatchValue(value="session")
            ),
            FieldCondition(
                key="metadata.user_id",
                match=MatchValue(value="user_1")
            ),
            FieldCondition(
                key="metadata.session_id",
                match=MatchValue(value="session_1")
            )
        ]
    )

    session_2_filter = Filter(
        must=[
            FieldCondition(
                key="metadata.scope",
                match=MatchValue(value="session")
            ),
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

    session_1_documents = retriever.invoke(
        "private project",
        filter=session_1_filter
    )

    session_2_documents = retriever.invoke(
        "private project",
        filter=session_2_filter
    )

    session_1_contents = [
        document.page_content
        for document in session_1_documents
    ]

    session_2_contents = [
        document.page_content
        for document in session_2_documents
    ]

    assert "Session one private project." in session_1_contents
    assert "Session two private project." not in session_1_contents

    assert "Session two private project." in session_2_contents
    assert "Session one private project." not in session_2_contents

def test_bm25_portfolio_and_session_use_separate_combined_indexes(vector_store):

    from langchain_core.documents import Document

    vector_store.add_documents([
        Document(
            page_content="Portfolio project: Meowski RAG chatbot.",
            metadata={
                "scope": "portfolio"
            }
        ),
        Document(
            page_content="Session one private project.",
            metadata={
                "scope": "session",
                "user_id": "user_1",
                "session_id": "session_1"
            }
        ),
        Document(
            page_content="Session two private project.",
            metadata={
                "scope": "session",
                "user_id": "user_1",
                "session_id": "session_2"
            }
        )
    ])

    index_service = BM25IndexService()

    retriever = create_bm25_retriever(
        vector_store=vector_store,
        k=10,
        index_service=index_service
    )

    session_1_filter = create_access_filter(
        user_id="user_1",
        session_id="session_1"
    )

    session_2_filter = create_access_filter(
        user_id="user_1",
        session_id="session_2"
    )

    session_1_documents = retriever.invoke(
        "project",
        filter=session_1_filter
    )

    session_2_documents = retriever.invoke(
        "project",
        filter=session_2_filter
    )

    session_1_contents = [
        document.page_content
        for document in session_1_documents
    ]

    session_2_contents = [
        document.page_content
        for document in session_2_documents
    ]

    assert "Portfolio project: Meowski RAG chatbot." in session_1_contents
    assert "Session one private project." in session_1_contents
    assert "Session two private project." not in session_1_contents

    assert "Portfolio project: Meowski RAG chatbot." in session_2_contents
    assert "Session two private project." in session_2_contents
    assert "Session one private project." not in session_2_contents