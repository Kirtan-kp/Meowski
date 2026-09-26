from langchain_core.runnables import Runnable
from app.llm.exceptions import LLMQuotaExceededError
from app.llm.exceptions import LLMError
from app.services.provider_circuit_breaker import (
    ProviderCircuitBreaker,
    ProviderCircuitOpenError,
)


class ProviderRouter(Runnable):
    """Try explicitly configured zero-cost providers in order."""

    def __init__(self, providers: list[tuple[str, Runnable]], breaker=None):
        self.providers = providers
        self.breaker = breaker or ProviderCircuitBreaker()

    def invoke(self, input, config=None, **kwargs):
        last_error = None
        for provider_name, provider in self.providers:
            try:
                self.breaker.before_call(provider_name)
            except (ProviderCircuitOpenError, LLMError) as exc:
                last_error = exc
                continue

            try:
                result = provider.invoke(input, config=config, **kwargs)
                self.breaker.record_success(provider_name)
                return result
            except LLMQuotaExceededError:
                raise
            except Exception as exc:
                self.breaker.record_failure(provider_name)
                last_error = exc

        if last_error is not None:
            raise last_error
        raise RuntimeError("No LLM providers are available")

    async def ainvoke(self, input, config=None, **kwargs):
        last_error = None
        for provider_name, provider in self.providers:
            try:
                self.breaker.before_call(provider_name)
            except (ProviderCircuitOpenError, LLMError) as exc:
                last_error = exc
                continue

            try:
                result = await provider.ainvoke(input, config=config, **kwargs)
                self.breaker.record_success(provider_name)
                return result
            except LLMQuotaExceededError:
                raise
            except Exception as exc:
                self.breaker.record_failure(provider_name)
                last_error = exc

        if last_error is not None:
            raise last_error
        raise RuntimeError("No LLM providers are available")
