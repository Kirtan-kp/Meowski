from langchain_core.retrievers import BaseRetriever
from app.retrieval.vector_retriever import create_vector_retriever
from app.retrieval.bm25_retriever import create_bm25_retriever
from app.retrieval.multi_query_retriever import create_multi_query_retriever
from app.retrieval.reranker import create_reranker

class RuntimeFilteredEnsembleRetriever(BaseRetriever):

    vector_retriever: object
    bm25_retriever: object
    weights: list[float]

    def _matches_filter(self , document , filter):
        if filter is None:
            return True

        metadata = document.metadata or {}

        for condition in filter.must:
            key = condition.key

            if key.startswith("metadata."):
                key = key[len("metadata."):]

            expected_value = condition.match.value
            actual_value = metadata.get(key)

            if actual_value != expected_value:
                return False

        return True

    def _get_relevant_documents(self , query , * , run_manager , filter = None):

        vector_documents = self.vector_retriever.invoke(query , filter = filter)

        bm25_documents = self.bm25_retriever._get_relevant_documents(query , run_manager = run_manager , filter = filter)

        ranked_documents = {}

        for rank, document in enumerate(vector_documents):
            if not self._matches_filter(document , filter):
                continue

            key = (document.page_content , str(document.metadata))
            ranked_documents.setdefault(key , [document, 0])
            ranked_documents[key][1] += (self.weights[0] / (60 + rank + 1))

        for rank , document in enumerate(bm25_documents):
            if not self._matches_filter(document , filter):
                continue

            key = (document.page_content, str(document.metadata))
            ranked_documents.setdefault(key, [document, 0])
            ranked_documents[key][1] += (self.weights[1] / (60 + rank + 1))

        results = sorted(ranked_documents.values() , key = lambda item : item[1] , reverse = True)

        return [document for document , score in results if self._matches_filter(document, filter)]


def create_retrieval_pipeline(vector_store , llm , k: int = 10 , top_n: int = 3 , search_type: str = "mmr", search_kwargs: dict | None = None , filter = None) -> BaseRetriever:

    vector_retriever = create_vector_retriever(vector_store = vector_store , k = k , search_type = search_type , search_kwargs = search_kwargs )

    bm25_retriever = create_bm25_retriever(vector_store = vector_store , filter = filter , k = k)

    hybrid_retriever = RuntimeFilteredEnsembleRetriever(vector_retriever = vector_retriever , bm25_retriever = bm25_retriever , weights = [0.5, 0.5])

    multi_query_retriever = create_multi_query_retriever(retriever = hybrid_retriever , llm = llm)

    reranker = create_reranker(retriever = multi_query_retriever , top_n = top_n)

    return reranker

