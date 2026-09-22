from app.core.config import settings
from app.llm.base import BaseLLM
from app.llm.providers.groq import GroqLLM
from app.llm.providers.ollama import OllamaLLM
from app.llm.guarded import QuotaGuardedLLM
from app.llm.resilient import ProviderRouter
from app.services.llm_quota_service import LLMQuotaService
from app.services.provider_circuit_breaker import ProviderCircuitBreaker


class ProviderRouterLLM(BaseLLM):
    def __init__(self, providers):
        self.providers = providers
        self._llm = ProviderRouter(providers, breaker=ProviderCircuitBreaker())

    @property
    def llm(self):
        return self._llm

    async def generate(self, prompt: str) -> str:
        response = await self._llm.ainvoke(prompt)
        return response.content if hasattr(response, "content") else str(response)


def _provider_llm(name: str, quota: LLMQuotaService):
    if name == "groq":
        provider = GroqLLM()
        model = settings.llm_model
    elif name == "ollama":
        provider = OllamaLLM()
        model = settings.ollama_model
    else:
        raise ValueError(f"Unsupported LLM provider: {name}")

    return QuotaGuardedLLM(
        provider.llm,
        quota,
        provider_name=name,
        model=model,
    )


def create_llm() -> BaseLLM:
    providers = []
    quota = LLMQuotaService()

    configured = [settings.llm_provider, *settings.llm_fallback_provider_list]
    seen = set()

    for name in configured:
        if name in seen or not settings.is_provider_enabled(name):
            continue
        seen.add(name)
        providers.append((name, _provider_llm(name, quota)))

    if not providers:
        raise ValueError("No enabled zero-cost LLM providers are configured")

    return ProviderRouterLLM(providers)