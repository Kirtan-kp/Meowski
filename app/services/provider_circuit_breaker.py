import time
import hashlib

import redis

from app.core.config import settings
from app.llm.exceptions import LLMProviderDisabledError, LLMProviderError


class ProviderCircuitOpenError(LLMProviderError):
    """Raised when a provider is temporarily isolated after repeated failures."""


class ProviderCircuitBreaker:
    """Redis-backed circuit breaker shared across application instances."""

    def __init__(self, redis_client=None):
        self.redis = redis_client or redis.Redis.from_url(
            settings.redis_cache_url,
            decode_responses=True,
        )

    def _scope(self, provider: str) -> str:
        return hashlib.sha256(provider.encode("utf-8")).hexdigest()[:16]

    def _failure_key(self, provider: str) -> str:
        return f"llm:circuit:failures:{self._scope(provider)}"

    def _open_key(self, provider: str) -> str:
        return f"llm:circuit:open_until:{self._scope(provider)}"

    def before_call(self, provider: str) -> None:
        if not settings.is_provider_enabled(provider):
            raise LLMProviderDisabledError(
                f"LLM provider '{provider}' is disabled by application policy"
            )

        open_until = self.redis.get(self._open_key(provider))
        if open_until is not None and float(open_until) > time.time():
            raise ProviderCircuitOpenError(
                "The LLM provider is temporarily unavailable. Please try again shortly."
            )

        if open_until is not None:
            self.redis.delete(self._open_key(provider))
            self.redis.delete(self._failure_key(provider))

    def record_success(self, provider: str) -> None:
        self.redis.delete(self._failure_key(provider))
        self.redis.delete(self._open_key(provider))

    def record_failure(self, provider: str) -> None:
        key = self._failure_key(provider)
        failures = self.redis.incr(key)
        self.redis.expire(key, settings.llm_provider_circuit_cooldown_seconds)

        if failures >= settings.llm_provider_failure_threshold:
            self.redis.setex(
                self._open_key(provider),
                settings.llm_provider_circuit_cooldown_seconds,
                time.time() + settings.llm_provider_circuit_cooldown_seconds,
            )
