from app.core.config import settings
from app.llm.base import BaseLLM
from langchain_groq import ChatGroq
from app.llm.exceptions import LLMProviderError,LLMRateLimitError,LLMTimeoutError

class GroqLLM(BaseLLM):

    def __init__(self):

        self.api_key = settings.llm_api_key
        extra = {}
        # Reasoning models count their hidden thinking against max_tokens. A low effort leaves room for the visible answer.
        effort = settings.llm_reasoning_effort or ("low" if "gpt-oss" in settings.llm_model.lower() else "")
        if effort:
            extra["reasoning_effort"] = effort
        self._llm = ChatGroq(api_key = self.api_key , model = settings.llm_model , 
                            timeout = settings.llm_timeout_seconds , max_retries = settings.llm_max_retries,
                            max_tokens = settings.llm_max_output_tokens , **extra)

    @property
    def llm(self):
        return self._llm

    async def generate(self , prompt : str) -> str:

        try:
            response = await self._llm.ainvoke(prompt)

        except TimeoutError as exc:
            raise LLMTimeoutError("LLM provider request timed out") from exc

        except Exception as exc:
            error_message = str(exc).lower()

            if "rate limit" in error_message or "429" in error_message:
                raise LLMRateLimitError("LLM provider rate limit exceeded") from exc

            raise LLMProviderError("LLM provider request failed") from exc
        
        return response.content