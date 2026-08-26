from langchain_core.retrievers import BaseRetriever

def create_vector_retriever(vector_store , k : int = 5 , 
                            search_type : str = "similarity" , search_kwargs : dict | None = None , filter = None) -> BaseRetriever:

    kwargs = {"k" : k}

    if search_kwargs:
        kwargs.update(search_kwargs)   #additional kwargs are added for example - {"k": 3, "filter": {"user_id": "user_101"}}

    if filter:
        kwargs["filter"] = filter

    return vector_store.as_retriever(search_type = search_type , search_kwargs = kwargs)