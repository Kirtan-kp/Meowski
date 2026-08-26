from langchain_core.retrievers import BaseRetriever

def create_vector_retriever(vector_store , k : int = 5) -> BaseRetriever:

    return vector_store.as_retriever(search_type = "similarity" , search_kwargs = {"k" : k})