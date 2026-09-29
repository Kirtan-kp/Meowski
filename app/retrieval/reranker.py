import os
from flashrank import Ranker
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_community.document_compressors import FlashrankRerank


def create_reranker(retriever , top_n : int = 5):

    compressor = FlashrankRerank(top_n = top_n , client = Ranker(cache_dir = os.environ.get("FLASHRANK_CACHE_DIR", "/tmp")))

    return ContextualCompressionRetriever(base_compressor = compressor , base_retriever = retriever)