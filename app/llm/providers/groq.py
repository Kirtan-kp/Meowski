from app.core.config import settings
from app.llm.base import BaseLLM
from langchain_groq import ChatGroq

class GroqLLM(BaseLLM):

    def __init__(self):

        self.api_key = settings.llm_api_key
        self._llm = ChatGroq(api_key = self.api_key , model = settings.llm_model)

    @property
    def llm(self):
        return self._llm

    async def generate(self , prompt : str) -> str:

        response = await self._llm.ainvoke(prompt)
        
        return response.content