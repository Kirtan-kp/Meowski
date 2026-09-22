import httpx
from langchain_core.runnables import Runnable

from app.core.config import settings
from app.llm.base import BaseLLM
from app.llm.exceptions import LLMProviderError, LLMTimeoutError


class OllamaRunnable(Runnable):
    def _prompt(self, value) -> str:
        if hasattr(value, "to_string"):
            return value.to_string()
        return str(value)

    def invoke(self, input, config=None, **kwargs):
        try:
            with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
                response = client.post(
                    f"{settings.ollama_base_url.rstrip('/')}/api/chat",
                    json={
                        "model": settings.ollama_model,
                        "messages": [{"role": "user", "content": self._prompt(input)}],
                        "stream": False,
                    },
                )
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError("LLM provider request timed out") from exc
        except Exception as exc:
            raise LLMProviderError("LLM provider request failed") from exc

        return data["message"]["content"]

    async def ainvoke(self, input, config=None, **kwargs):
        try:
            async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
                response = await client.post(
                    f"{settings.ollama_base_url.rstrip('/')}/api/chat",
                    json={
                        "model": settings.ollama_model,
                        "messages": [{"role": "user", "content": self._prompt(input)}],
                        "stream": False,
                    },
                )
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError("LLM provider request timed out") from exc
        except Exception as exc:
            raise LLMProviderError("LLM provider request failed") from exc

        return data["message"]["content"]


class OllamaLLM(BaseLLM):
    def __init__(self):
        self._llm = OllamaRunnable()

    @property
    def llm(self):
        return self._llm

    async def generate(self, prompt: str) -> str:
        return await self._llm.ainvoke(prompt)
