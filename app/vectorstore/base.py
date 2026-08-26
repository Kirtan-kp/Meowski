from abc import ABC,abstractmethod

class VectorStore(ABC):

    @abstractmethod
    def add_documents(self , documents):
        pass

    @abstractmethod
    def similarity_search(self , query , k = 5 , **kwargs):
        pass

    @abstractmethod
    def delete(self , **kwargs):  # kwargs is a dict of the keyword args passed to the function
        pass