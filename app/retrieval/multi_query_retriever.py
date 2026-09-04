from langchain_classic.retrievers import MultiQueryRetriever

class RuntimeFilteredMultiQueryRetriever(MultiQueryRetriever):

    def _get_relevant_documents(self , query , * , run_manager , filter = None):

        queries = self.generate_queries(query, run_manager)

        if self.include_original:
            queries.append(query)

        documents = []

        for generated_query in queries:
            result = self.retriever.invoke(generated_query , filter = filter)
            documents.extend(result)

        unique_documents = []
        seen = set()

        for document in documents:
            key = (document.page_content , str(document.metadata))

            if key not in seen:
                seen.add(key)
                unique_documents.append(document)

        return unique_documents

def create_multi_query_retriever(retriever, llm):

    base_retriever = MultiQueryRetriever.from_llm(retriever = retriever , llm = llm)

    return RuntimeFilteredMultiQueryRetriever(retriever = base_retriever.retriever , 
                                              llm_chain = base_retriever.llm_chain , 
                                              include_original = base_retriever.include_original)