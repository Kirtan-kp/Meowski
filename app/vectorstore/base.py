from abc import ABC,abstractmethod

class VectorStore(ABC):

    @abstractmethod
    def add_chunks(self , chunks):
        pass

    @abstractmethod
    def search(self , query_vector , top_k = 5 , filters = None):
        pass

    @abstractmethod
    def delete_document(self , document_id):
        pass