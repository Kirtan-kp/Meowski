from contextvars import ContextVar
from langchain_core.runnables import Runnable
from app.services.llm_quota_service import LLMQuotaService
from app.api.dependencies import get_observability_service
from app.core.config import settings
from app.llm.exceptions import LLMConcurrencyLimitError

_llm_request_context: ContextVar[tuple[str, str] | None] = ContextVar(
    "llm_request_context", default=None
)

def set_llm_request_context(user_id: str, session_id: str):
    return _llm_request_context.set((user_id, session_id))

def reset_llm_request_context(token):
    _llm_request_context.reset(token)

class QuotaGuardedLLM(Runnable):
    """Runnable adapter that enforces token budgets before every provider call."""

    def __init__(self, llm, quota_service: LLMQuotaService):
        self.llm = llm
        self.quota_service = quota_service

    def _context(self):
        context = _llm_request_context.get()
        if context is None:
            return "system", "system"
        return context

    def invoke(self, input, config=None, **kwargs):
        user_id, session_id = self._context()
        estimated_tokens = self.quota_service.reserve(
            input,
            user_id=user_id,
            session_id=session_id,
        )
        observability = get_observability_service()

        observability.record_llm(
            provider=settings.llm_provider,
            model=settings.llm_model,
            estimated_tokens=estimated_tokens,
        )
        try:
            concurrency_key = self.quota_service.acquire_concurrency()
        except LLMConcurrencyLimitError:
            get_observability_service().record_quota(
                "concurrency_blocked"
            )
            raise
        try:
            return self.llm.invoke(input, config=config, **kwargs)
        finally:
            self.quota_service.release_concurrency(concurrency_key)

    async def ainvoke(self, input, config=None, **kwargs):
        user_id, session_id = self._context()
        estimated_tokens = self.quota_service.reserve(
            input,
            user_id=user_id,
            session_id=session_id,
        )
        observability = get_observability_service()

        observability.record_llm(
            provider=settings.llm_provider,
            model=settings.llm_model,
            estimated_tokens=estimated_tokens,
        )
        try:
            concurrency_key = self.quota_service.acquire_concurrency()
        except LLMConcurrencyLimitError:
            get_observability_service().record_quota(
                "concurrency_blocked"
            )
            raise
        try:
            return await self.llm.ainvoke(input, config=config, **kwargs)
        finally:
            self.quota_service.release_concurrency(concurrency_key)
