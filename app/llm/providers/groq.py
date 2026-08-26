from app.core.config import settings
from app.llm.base import BaseLLM

class GroqLLM(BaseLLM):

    def __init__(self):
        self.api_key = settings.llm_api_key

    async def generate(self , prompt: str) -> str:
        pass