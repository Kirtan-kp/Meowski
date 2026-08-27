from langchain_core.retrievers import BaseRetriever
from app.retrieval.vector_retriever import create_vector_retriever
from app.retrieval.multi_query_retriever import create_multi_query_retriever
from app.retrieval.reranker import create_reranker

def create_retrieval_pipeline(vector_store , llm , k: int = 10 , top_n: int = 3 , search_type: str = "mmr", search_kwargs: dict | None = None , filter = None) -> BaseRetriever:

    vector_retriever = create_vector_retriever(vector_store = vector_store , k = k , search_type = search_type , search_kwargs = search_kwargs , filter = filter)

    multi_query_retriever = create_multi_query_retriever(retriever = vector_retriever , llm = llm)

    reranker = create_reranker(retriever = multi_query_retriever , top_n = top_n)

    return reranker

