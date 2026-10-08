from contextvars import ContextVar
from langchain_core.runnables import Runnable
from app.services.llm_quota_service import LLMQuotaService
from app.api.dependencies import get_observability_service
from app.llm.exceptions import LLMConcurrencyLimitError, LLMRateLimitError, LLMTimeoutError, LLMProviderError
from app.core.config import settings

_llm_request_context: ContextVar[tuple[str, str] | None] = ContextVar(
    "llm_request_context", default=None
)

def set_llm_request_context(user_id: str, session_id: str):
    return _llm_request_context.set((user_id, session_id))

def reset_llm_request_context(token):
    _llm_request_context.reset(token)

class QuotaGuardedLLM(Runnable):
    """Runnable adapter that enforces token budgets and concurrency before provider calls."""

    def __init__(self, llm, quota_service: LLMQuotaService, provider_name: str | None = None, model: str | None = None):
        self.llm = llm
        self.quota_service = quota_service
        self.provider_name = provider_name or settings.llm_provider
        self.model = model or settings.llm_model

    def _normalize_error(self, exc):
        if isinstance(exc, (LLMRateLimitError, LLMTimeoutError, LLMProviderError, LLMConcurrencyLimitError)):
            return exc
        if isinstance(exc, TimeoutError):
            return LLMTimeoutError("LLM provider request timed out")
        message = str(exc).lower()
        if "rate limit" in message or "429" in message:
            return LLMRateLimitError("LLM provider rate limit exceeded")
        return LLMProviderError("LLM provider request failed")

    def _context(self):
        context = _llm_request_context.get()
        if context is None:
            return "system", "system"
        return context


    def _record_usage(self, response):
        usage = getattr(response, "usage_metadata", None) or getattr(response, "response_metadata", {}).get("token_usage")
        if not isinstance(usage, dict):
            return None

        input_tokens = usage.get("input_tokens", usage.get("prompt_tokens"))
        output_tokens = usage.get("output_tokens", usage.get("completion_tokens"))
        total_tokens = usage.get("total_tokens")

        if total_tokens is None and input_tokens is not None and output_tokens is not None:
            total_tokens = input_tokens + output_tokens

        get_observability_service().record_llm_usage(
            provider=self.provider_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
        )
        return total_tokens

    def invoke(self, input, config=None, **kwargs):
        user_id, session_id = self._context()
        estimated_tokens = self.quota_service.reserve(
            input,
            user_id=user_id,
            session_id=session_id,
            provider=self.provider_name,
        )
        concurrency_key = None
        try:
            concurrency_key = self.quota_service.acquire_concurrency(self.provider_name)
            get_observability_service().record_llm(
                provider=self.provider_name,
                model=self.model,
                estimated_tokens=estimated_tokens,
            )
            try:
                response = self.llm.invoke(input, config=config, **kwargs)
                self.quota_service.settle(estimated_tokens, self._record_usage(response))
                return response
            except Exception as exc:
                self.quota_service.settle(estimated_tokens, 0)  # nothing was generated: give the reservation back
                raise self._normalize_error(exc) from exc
        except LLMConcurrencyLimitError:
            get_observability_service().record_quota("concurrency_blocked")
            raise
        finally:
            if concurrency_key is not None:
                self.quota_service.release_concurrency(concurrency_key)

    async def ainvoke(self, input, config=None, **kwargs):
        user_id, session_id = self._context()
        estimated_tokens = self.quota_service.reserve(
            input,
            user_id=user_id,
            session_id=session_id,
            provider=self.provider_name,
        )
        concurrency_key = None
        try:
            concurrency_key = self.quota_service.acquire_concurrency(self.provider_name)
            get_observability_service().record_llm(
                provider=self.provider_name,
                model=self.model,
                estimated_tokens=estimated_tokens,
            )
            try:
                response = await self.llm.ainvoke(input, config=config, **kwargs)
                self.quota_service.settle(estimated_tokens, self._record_usage(response))
                return response
            except Exception as exc:
                self.quota_service.settle(estimated_tokens, 0)
                raise self._normalize_error(exc) from exc
        except LLMConcurrencyLimitError:
            get_observability_service().record_quota("concurrency_blocked")
            raise
        finally:
            if concurrency_key is not None:
                self.quota_service.release_concurrency(concurrency_key)