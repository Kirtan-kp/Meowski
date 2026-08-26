from langchain_classic.retrievers import MultiQueryRetriever

def create_multi_query_retriever(retriever , llm):

    return MultiQueryRetriever.from_llm(retriever = retriever , llm = llm)  #generate multiple alternative queries and retrieving documents for them