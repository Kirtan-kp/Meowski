import asyncio
import pytest
from app.llm.exceptions import LLMProviderError,LLMRateLimitError,LLMTimeoutError
from app.llm.providers.groq import GroqLLM


class FakeLLM:

    def __init__(self, error=None):
        self.error = error

    async def ainvoke(self, prompt):

        if self.error:
            raise self.error

        class Response:
            content = "Test response"

        return Response()


def create_groq_llm(fake_llm):

    service = GroqLLM.__new__(GroqLLM)
    service._llm = fake_llm

    return service


def test_groq_llm_generate_success():

    service = create_groq_llm(FakeLLM())

    result = asyncio.run(
        service.generate("Hello")
    )

    assert result == "Test response"


def test_groq_llm_generate_timeout():

    service = create_groq_llm(
        FakeLLM(error=TimeoutError())
    )

    with pytest.raises(LLMTimeoutError):
        asyncio.run(
            service.generate("Hello")
        )


def test_groq_llm_generate_rate_limit():

    service = create_groq_llm(
        FakeLLM(error=Exception("429 rate limit exceeded"))
    )

    with pytest.raises(LLMRateLimitError):
        asyncio.run(
            service.generate("Hello")
        )


def test_groq_llm_generate_provider_error():

    service = create_groq_llm(
        FakeLLM(error=Exception("connection failed"))
    )

    with pytest.raises(LLMProviderError):
        asyncio.run(
            service.generate("Hello")
        )

def test_groq_llm_configures_timeout_and_retries(monkeypatch):

    monkeypatch.setattr(
        "app.llm.providers.groq.ChatGroq",
        lambda **kwargs: kwargs,
    )

    from app.core.config import settings
    from app.llm.providers.groq import GroqLLM

    llm = GroqLLM()

    assert llm.llm["timeout"] == settings.llm_timeout_seconds
    assert llm.llm["max_retries"] == settings.llm_max_retries