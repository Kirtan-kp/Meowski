from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from app.services.bm25_index_service import BM25IndexService

class SessionAwareBM25Retriever(BaseRetriever):

    vector_store: object
    k : int = 10
    index_service: object

    def _cache_key(self, filter):
        if filter is None:
            raise ValueError("BM25 retrieval requires an access filter.")

        if filter.must:
            metadata = {
                condition.key: condition.match.value
                for condition in filter.must
                if condition.match is not None
            }

            # Explicit session-scoped filter
            if metadata.get("metadata.scope") == "session":
                user_id = metadata.get("metadata.user_id")
                session_id = metadata.get("metadata.session_id")

                if user_id and session_id:
                    return BM25IndexService.session_cache_key(
                        user_id,
                        session_id,
                    )

            # Existing user + session filter format
            if (
                metadata.get("metadata.user_id")
                and metadata.get("metadata.session_id")
            ):
                return BM25IndexService.session_cache_key(
                    metadata["metadata.user_id"],
                    metadata["metadata.session_id"],
                )

            # Portfolio-only filter
            if metadata.get("metadata.scope") == "portfolio":
                return BM25IndexService.portfolio_cache_key()

        if filter.should:
            has_portfolio = False
            session_user_id = None
            session_id = None

            for condition in filter.should:
                if not condition.must:
                    continue

                metadata = {
                    item.key: item.match.value
                    for item in condition.must
                    if item.match is not None
                }

                if metadata.get("metadata.scope") == "portfolio":
                    has_portfolio = True

                if metadata.get("metadata.scope") == "session":
                    session_user_id = metadata.get("metadata.user_id")
                    session_id = metadata.get("metadata.session_id")

            if has_portfolio and session_user_id and session_id:
                return BM25IndexService.portfolio_session_cache_key(
                    session_user_id,
                    session_id,
                )

            if session_user_id and session_id:
                return BM25IndexService.session_cache_key(
                    session_user_id,
                    session_id,
                )

            if has_portfolio:
                return BM25IndexService.portfolio_cache_key()

        raise ValueError("Unsupported BM25 access filter.")

    def _load_documents(self, filter):
        documents = []
        offset = None

        while True:
            points, offset = self.vector_store.client.scroll(
                collection_name=self.vector_store.collection_name,
                scroll_filter=filter,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )

            for point in points:
                payload = point.payload or {}

                page_content = payload.get(
                    "page_content",
                    ""
                )

                metadata = payload.get(
                    "metadata",
                    {}
                ).copy()

                metadata["_id"] = str(point.id)

                if page_content:
                    documents.append(
                        Document(
                            page_content=page_content,
                            metadata=metadata
                        )
                    )

            if offset is None:
                break

        return documents

    def _get_relevant_documents(self , query , * , run_manager , filter = None):

        if filter is None:
            raise ValueError("BM25 retrieval requires an access filter.")
        
        cache_key = self._cache_key(filter)

        retriever = self.index_service.get_or_create(
            cache_key=cache_key,
            loader=lambda: self._load_documents(filter),
            k=self.k
        )

        if retriever is None:
            return []

        return retriever.invoke(query)

def create_bm25_retriever(vector_store , filter = None , k : int = 10 , index_service : BM25IndexService | None = None):

    if index_service is None:
        index_service = BM25IndexService()

    return SessionAwareBM25Retriever(vector_store = vector_store , k = k , index_service = index_service)