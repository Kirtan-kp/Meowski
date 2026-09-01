from langchain_core.retrievers import BaseRetriever
from langchain_classic.retrievers import EnsembleRetriever
from app.retrieval.vector_retriever import create_vector_retriever
from app.retrieval.bm25_retriever import create_bm25_retriever
from app.retrieval.multi_query_retriever import create_multi_query_retriever
from app.retrieval.reranker import create_reranker

def create_retrieval_pipeline(vector_store , llm , k: int = 10 , top_n: int = 3 , search_type: str = "mmr", search_kwargs: dict | None = None , filter = None) -> BaseRetriever:

    vector_retriever = create_vector_retriever(vector_store = vector_store , k = k , search_type = search_type , search_kwargs = search_kwargs , filter = filter)

    bm25_retriever = create_bm25_retriever(vector_store = vector_store , filter = filter , k = k)

    hybrid_retriever = EnsembleRetriever(retrievers = [vector_retriever , bm25_retriever] , weights = [0.5, 0.5])

    multi_query_retriever = create_multi_query_retriever(retriever = hybrid_retriever , llm = llm)

    reranker = create_reranker(retriever = multi_query_retriever , top_n = top_n)

    return reranker

