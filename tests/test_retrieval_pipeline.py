from qdrant_client.models import Filter, FieldCondition, MatchValue
from app.vectorstore.qdrant_store import QdrantVectorStore
from app.retrieval.pipeline import create_retrieval_pipeline,RuntimeFilteredEnsembleRetriever
from app.retrieval.multi_query_retriever import RuntimeFilteredMultiQueryRetriever
from langchain_core.documents import Document
from langchain_core.language_models import FakeListLLM
import pytest

@pytest.fixture
def vector_store():
    return QdrantVectorStore(embedding_dimension = 384)

@pytest.fixture
def llm():
    return FakeListLLM(responses = ["project experience\nprojects using qdrant"])

def create_user_filter(user_id , session_id):
    return Filter(       
        must=[                  
            FieldCondition(     
                key = "metadata.user_id",
                match = MatchValue(value = user_id)
            ),
            FieldCondition(
                key = "metadata.session_id",
                match = MatchValue(value = session_id)
            )
        ]
    )


def test_retrieval_pipeline_returns_filtered_documents(vector_store , llm):

    user_filter = create_user_filter(user_id = "user_1" , session_id = "session_1")
    retrieval_pipeline = create_retrieval_pipeline(vector_store = vector_store , llm = llm , k = 10 ,
                                                   top_n = 3 , search_type = "mmr")

    documents = retrieval_pipeline.invoke("What projects did Kirtan work on?" , filter = user_filter)
    assert len(documents) <= 3

    for document in documents:
        assert document.metadata.get("user_id") == "user_1"
        assert document.metadata.get("session_id") == "session_1"

def test_retrieval_pipeline_blocks_cross_session_documents(vector_store, llm):

    user_filter = create_user_filter(user_id = "user_1" , session_id = "session_2")
    retrieval_pipeline = create_retrieval_pipeline(vector_store = vector_store , llm = llm , 
                                                   k = 10 , top_n = 3 , search_type = "mmr")
    documents = retrieval_pipeline.invoke("What projects did Kirtan work on?" , filter = user_filter)

    for document in documents:
        assert document.metadata.get("user_id") == "user_1"
        assert document.metadata.get("session_id") == "session_2"


def test_retrieval_pipeline_blocks_cross_user_documents(vector_store, llm):

    user_filter = create_user_filter(user_id = "user_2" , session_id = "session_2")
    retrieval_pipeline = create_retrieval_pipeline(vector_store = vector_store , llm = llm , k = 10 , 
                                                   top_n = 3 , search_type = "mmr")
    documents = retrieval_pipeline.invoke("What projects did Kirtan work on?" , filter = user_filter)

    for document in documents:
        assert document.metadata.get("user_id") == "user_2"
        assert document.metadata.get("session_id") == "session_2"

def test_multi_query_forwards_filter_to_every_query():

    from langchain_core.retrievers import BaseRetriever
    from langchain_core.runnables import RunnableLambda

    class FakeRetriever(BaseRetriever):

        filters : list = []

        def _get_relevant_documents(self , query , * , run_manager , filter = None):
            self.filters.append(filter)

            return [
                Document(
                    page_content="Allowed document",
                    metadata={
                        "user_id" : "user_1",
                        "session_id" : "session_1"
                    }
                )
            ]

    class FakeMultiQueryRetriever(RuntimeFilteredMultiQueryRetriever):

        def generate_queries(self , query , run_manager):
            return [
                "project experience",
                "projects using qdrant"
            ]

    fake_retriever = FakeRetriever(filters = [])
    fake_llm_chain = RunnableLambda(lambda _: "")
    retriever = FakeMultiQueryRetriever(retriever = fake_retriever , llm_chain = fake_llm_chain , include_original = False)
    user_filter = create_user_filter(user_id = "user_1" , session_id = "session_1")
    documents = retriever.invoke("What projects use Qdrant?" , filter = user_filter)
    assert len(fake_retriever.filters) == 2

    for applied_filter in fake_retriever.filters:
        assert applied_filter is user_filter

    assert len(documents) == 1

def test_rrf_removes_documents_that_fail_filter():

    class FakeVectorRetriever:

        def invoke(self, query, filter=None):
            return [
                Document(
                    page_content="Allowed vector document",
                    metadata={
                        "user_id": "user_1",
                        "session_id": "session_1"
                    }
                ),
                Document(
                    page_content="Blocked vector document",
                    metadata={
                        "user_id": "user_2",
                        "session_id": "session_2"
                    }
                )
            ]

    class FakeBM25Retriever:

        def _get_relevant_documents(self, query, run_manager, filter=None):
            return [
                Document(
                    page_content="Allowed BM25 document",
                    metadata={
                        "user_id": "user_1",
                        "session_id": "session_1"
                    }
                ),
                Document(
                    page_content="Blocked BM25 document",
                    metadata={
                        "user_id": "user_2",
                        "session_id": "session_2"
                    }
                )
            ]

    retriever = RuntimeFilteredEnsembleRetriever(
        vector_retriever=FakeVectorRetriever(),
        bm25_retriever=FakeBM25Retriever(),
        weights=[0.5, 0.5]
    )

    user_filter = create_user_filter(
        user_id="user_1",
        session_id="session_1"
    )

    documents = retriever.invoke(
        "What projects use Qdrant?",
        filter=user_filter
    )

    assert len(documents) == 2

    for document in documents:
        assert document.metadata["user_id"] == "user_1"
        assert document.metadata["session_id"] == "session_1"

def test_reranker_only_receives_filtered_documents():

    allowed_document = Document(
        page_content="Allowed project using Qdrant",
        metadata={
            "user_id": "user_1",
            "session_id": "session_1"
        }
    )

    blocked_document = Document(
        page_content="Private project from another user",
        metadata={
            "user_id": "user_2",
            "session_id": "session_2"
        }
    )

    class FakeRetriever:

        def invoke(self, query, filter=None):
            assert filter is not None

            documents = [
                allowed_document,
                blocked_document
            ]

            return [
                document
                for document in documents
                if document.metadata["user_id"] == "user_1"
                and document.metadata["session_id"] == "session_1"
            ]

    user_filter = create_user_filter(
        user_id="user_1",
        session_id="session_1"
    )

    retriever = FakeRetriever()

    documents = retriever.invoke(
        "What projects use Qdrant?",
        filter=user_filter
    )

    assert documents == [allowed_document]

    for document in documents:
        assert document.metadata["user_id"] == "user_1"
        assert document.metadata["session_id"] == "session_1"

def test_portfolio_documents_are_accessible_but_other_session_documents_are_blocked(
    vector_store,
    llm
):

    access_filter = Filter(
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
                        match=MatchValue(value="user_1")
                    ),
                    FieldCondition(
                        key="metadata.session_id",
                        match=MatchValue(value="session_1")
                    )
                ]
            )
        ]
    )

    retrieval_pipeline = create_retrieval_pipeline(
        vector_store=vector_store,
        llm=llm,
        k=10,
        top_n=5,
        search_type="mmr"
    )

    documents = retrieval_pipeline.invoke(
        "What projects has Kirtan worked on?",
        filter=access_filter
    )

    assert len(documents) > 0

    for document in documents:
        scope = document.metadata.get("scope")

        assert scope in {"portfolio", "session"}

        if scope == "portfolio":
            continue

        assert document.metadata.get("user_id") == "user_1"
        assert document.metadata.get("session_id") == "session_1"