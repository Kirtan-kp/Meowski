from qdrant_client.models import Filter, FieldCondition, MatchValue
from app.vectorstore.qdrant_store import QdrantVectorStore
from app.retrieval.pipeline import create_retrieval_pipeline
from app.llm.providers.groq import GroqLLM
import pytest

@pytest.fixture
def vector_store():
    return QdrantVectorStore(embedding_dimension = 384)

@pytest.fixture
def llm():
    return GroqLLM()

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
    retrieval_pipeline = create_retrieval_pipeline(vector_store = vector_store , llm = llm.llm , k = 10 ,
                                                   top_n = 3 , search_type = "mmr")

    documents = retrieval_pipeline.invoke("What projects did Kirtan work on?" , filter = user_filter)
    assert len(documents) <= 3

    for document in documents:
        assert document.metadata.get("user_id") == "user_1"
        assert document.metadata.get("session_id") == "session_1"

def test_retrieval_pipeline_blocks_cross_session_documents(vector_store, llm):

    user_filter = create_user_filter(user_id = "user_1" , session_id = "session_2")
    retrieval_pipeline = create_retrieval_pipeline(vector_store = vector_store , llm = llm.llm , 
                                                   k = 10 , top_n = 3 , search_type = "mmr")
    documents = retrieval_pipeline.invoke("What projects did Kirtan work on?" , filter = user_filter)

    for document in documents:
        assert document.metadata.get("user_id") == "user_1"
        assert document.metadata.get("session_id") == "session_2"


def test_retrieval_pipeline_blocks_cross_user_documents(vector_store, llm):

    user_filter = create_user_filter(user_id = "user_2" , session_id = "session_2")
    retrieval_pipeline = create_retrieval_pipeline(vector_store = vector_store , llm = llm.llm , k = 10 , 
                                                   top_n = 3 , search_type = "mmr")
    documents = retrieval_pipeline.invoke("What projects did Kirtan work on?" , filter = user_filter)

    for document in documents:
        assert document.metadata.get("user_id") == "user_2"
        assert document.metadata.get("session_id") == "session_2"