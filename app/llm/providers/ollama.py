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
                        "options": {"num_predict": settings.llm_max_output_tokens},
                    },
                )
                response.raise_for_status()
                data = response.json()
                from app.api.dependencies import get_observability_service
                get_observability_service().record_llm_usage(
                    provider="ollama",
                    input_tokens=data.get("prompt_eval_count"),
                    output_tokens=data.get("eval_count"),
                    total_tokens=(data.get("prompt_eval_count", 0) + data.get("eval_count", 0))
                    if data.get("prompt_eval_count") is not None and data.get("eval_count") is not None
                    else None,
                )
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
                        "options": {"num_predict": settings.llm_max_output_tokens},
                    },
                )
                response.raise_for_status()
                data = response.json()
                from app.api.dependencies import get_observability_service
                get_observability_service().record_llm_usage(
                    provider="ollama",
                    input_tokens=data.get("prompt_eval_count"),
                    output_tokens=data.get("eval_count"),
                    total_tokens=(data.get("prompt_eval_count", 0) + data.get("eval_count", 0))
                    if data.get("prompt_eval_count") is not None and data.get("eval_count") is not None
                    else None,
                )
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
