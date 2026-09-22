import time
import pytest

from app.core.config import settings
from app.llm.exceptions import LLMProviderDisabledError
from app.services.provider_circuit_breaker import ProviderCircuitBreaker, ProviderCircuitOpenError


class FakeRedis:
    def __init__(self):
        self.data = {}
        self.counts = {}

    def get(self, key):
        value = self.data.get(key)
        if isinstance(value, tuple):
            expires, stored = value
            if expires <= time.time():
                self.data.pop(key, None)
                return None
            return stored
        return value

    def delete(self, key):
        self.data.pop(key, None)

    def incr(self, key):
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]

    def expire(self, key, seconds):
        return True

    def setex(self, key, seconds, value):
        self.data[key] = (time.time() + seconds, value)


def test_circuit_opens_after_repeated_failures(monkeypatch):
    redis = FakeRedis()
    breaker = ProviderCircuitBreaker(redis)
    monkeypatch.setattr(settings, "llm_provider_failure_threshold", 2)
    monkeypatch.setattr(settings, "llm_provider_circuit_cooldown_seconds", 30)

    breaker.record_failure("groq")
    breaker.record_failure("groq")

    with pytest.raises(ProviderCircuitOpenError):
        breaker.before_call("groq")


def test_success_closes_circuit():
    redis = FakeRedis()
    breaker = ProviderCircuitBreaker(redis)
    breaker.record_failure("groq")
    breaker.record_success("groq")
    breaker.before_call("groq")


def test_disabled_provider_is_rejected(monkeypatch):
    redis = FakeRedis()
    breaker = ProviderCircuitBreaker(redis)
    monkeypatch.setattr(settings, "llm_enabled_providers", "")

    with pytest.raises(LLMProviderDisabledError):
        breaker.before_call("groq")
