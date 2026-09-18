from abc import ABC,abstractmethod

class BaseLLM(ABC):

    @property
    @abstractmethod
    def llm(self):
        pass

    @abstractmethod
    async def generate( self , prompt : str ) -> str:
        pass