from langchain_core.documents import Document

from app.services.bm25_index_service import BM25IndexService


def test_bm25_index_is_built_only_once():

    service = BM25IndexService()

    calls = []

    def loader():
        calls.append(1)

        return [
            Document(
                page_content="cat project",
                metadata={"_id": "1"}
            )
        ]

    first = service.get_or_create(
        cache_key="session:user_1:session_1",
        loader=loader,
        k=5
    )

    second = service.get_or_create(
        cache_key="session:user_1:session_1",
        loader=loader,
        k=5
    )

    assert first is second
    assert len(calls) == 1


def test_bm25_indexes_are_isolated_by_cache_key():

    service = BM25IndexService()

    calls = []

    def loader():
        calls.append(1)

        return [
            Document(
                page_content="cat project",
                metadata={"_id": str(len(calls))}
            )
        ]

    first = service.get_or_create(
        cache_key="session:user_1:session_1",
        loader=loader,
        k=5
    )

    second = service.get_or_create(
        cache_key="session:user_2:session_2",
        loader=loader,
        k=5
    )

    assert first is not second
    assert len(calls) == 2


def test_bm25_session_invalidation():

    service = BM25IndexService()

    calls = []

    def loader():
        calls.append(1)

        return [
            Document(
                page_content="cat project",
                metadata={"_id": "1"}
            )
        ]

    key = service.session_cache_key(
        "user_1",
        "session_1"
    )

    first = service.get_or_create(
        cache_key=key,
        loader=loader,
        k=5
    )

    service.invalidate_session(
        user_id="user_1",
        session_id="session_1"
    )

    second = service.get_or_create(
        cache_key=key,
        loader=loader,
        k=5
    )

    assert first is not second
    assert len(calls) == 2


def test_bm25_empty_corpus_is_not_cached():

    service = BM25IndexService()

    calls = []

    def loader():
        calls.append(1)
        return []

    first = service.get_or_create(
        cache_key="session:user_1:session_1",
        loader=loader,
        k=5
    )

    second = service.get_or_create(
        cache_key="session:user_1:session_1",
        loader=loader,
        k=5
    )

    assert first is None
    assert second is None
    assert len(calls) == 2