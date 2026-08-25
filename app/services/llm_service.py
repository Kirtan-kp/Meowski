from app.llm.base import BaseLLM

class LLMService:

    def __init__(self , llm : BaseLLM):
        self.llm = llm

    async def generate(self , prompt : str) -> str:
        return await self.llm.generate(prompt)