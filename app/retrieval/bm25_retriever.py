from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

class SessionAwareBM25Retriever(BaseRetriever):

    vector_store: object
    k: int = 10

    def _get_relevant_documents(self, query, *, run_manager, filter=None):

        documents = []

        offset = None

        while True:

            points , offset = self.vector_store.client.scroll(collection_name = self.vector_store.collection_name , 
                                                        scroll_filter = filter , limit = 100 , offset = offset , 
                                                        with_payload = True , with_vectors = False)

            for point in points:
                payload = point.payload or {}
                page_content = payload.get("page_content", "")
                metadata = payload.get("metadata", {})

                if page_content:
                    documents.append(Document(page_content = page_content , metadata = metadata))

            if offset is None:
                break

        if not documents:
            return []

        retriever = BM25Retriever.from_documents(documents)
        retriever.k = self.k

        return retriever.invoke(query)

def create_bm25_retriever(vector_store , filter = None , k : int = 10):

    return SessionAwareBM25Retriever(vector_store = vector_store , k = k)