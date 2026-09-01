from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

def create_bm25_retriever(vector_store , filter = None , k : int = 10):

    documents = []

    offset = None

    while True:

        points , offset = vector_store.client.scroll(collection_name = vector_store.collection_name , 
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

    retriever = BM25Retriever.from_documents(documents)
    retriever.k = k

    return retriever