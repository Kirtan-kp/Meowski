from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from app.retrieval.pipeline import CachedRetriever


class FakeCache:
    def __init__(self):
        self.data = {}
        self.set_calls = 0
        self.version = 0

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value, ttl_seconds):
        self.data[key] = value
        self.set_calls += 1

    def delete(self, key):
        self.data.pop(key, None)

    def get_version(self):
        return self.version
    
    def increment(self, key):
        self.version += 1
        return self.version
    
class FakeRetriever(BaseRetriever):

    calls: int = 0

    def _get_relevant_documents(
        self,
        query,
        *,
        run_manager,
        filter=None
    ):
        self.calls += 1

        return [
            Document(
                page_content=f"Result for {query}",
                metadata={
                    "scope": "portfolio"
                }
            )
        ]


def test_retrieval_cache_hit():
    retriever = FakeRetriever()
    cache = FakeCache()

    cached_retriever = CachedRetriever(
        retriever=retriever,
        cache=cache
    )

    first = cached_retriever.invoke("What is Meowski?")
    second = cached_retriever.invoke("What is Meowski?")

    assert first == second
    assert retriever.calls == 1
    assert cache.set_calls == 1


def test_different_queries_do_not_share_cache():
    retriever = FakeRetriever()
    cache = FakeCache()

    cached_retriever = CachedRetriever(
        retriever=retriever,
        cache=cache
    )

    cached_retriever.invoke("What is Meowski?")
    cached_retriever.invoke("What is RAG?")

    assert retriever.calls == 2
    assert cache.set_calls == 2


def test_different_filters_do_not_share_cache():
    from qdrant_client.models import (
        Filter,
        FieldCondition,
        MatchValue
    )

    retriever = FakeRetriever()
    cache = FakeCache()

    cached_retriever = CachedRetriever(
        retriever=retriever,
        cache=cache
    )

    filter_one = Filter(
        must=[
            FieldCondition(
                key="metadata.user_id",
                match=MatchValue(value="user_1")
            )
        ]
    )

    filter_two = Filter(
        must=[
            FieldCondition(
                key="metadata.user_id",
                match=MatchValue(value="user_2")
            )
        ]
    )

    cached_retriever.invoke(
        "What is Meowski?",
        filter=filter_one
    )

    cached_retriever.invoke(
        "What is Meowski?",
        filter=filter_two
    )

    assert retriever.calls == 2
    assert cache.set_calls == 2

def test_same_filter_uses_cache():
    from qdrant_client.models import (
        Filter,
        FieldCondition,
        MatchValue
    )

    retriever = FakeRetriever()
    cache = FakeCache()

    cached_retriever = CachedRetriever(
        retriever=retriever,
        cache=cache
    )

    access_filter = Filter(
        must=[
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

    first = cached_retriever.invoke(
        "project",
        filter=access_filter
    )

    second = cached_retriever.invoke(
        "project",
        filter=access_filter
    )

    assert first == second
    assert retriever.calls == 1
    assert cache.set_calls == 1

def test_retrieval_cache_version_starts_at_zero():
    cache = FakeCache()
    assert cache.get_version() == 0


def test_retrieval_cache_version_increments():
    cache = FakeCache()

    assert cache.get_version() == 0

    cache.increment("cache:retrieval:document_version")

    assert cache.get_version() == 1

    cache.increment("cache:retrieval:document_version")

    assert cache.get_version() == 2