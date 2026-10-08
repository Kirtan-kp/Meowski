import pytest

from app.core.config import settings
from app.llm.exceptions import LLMQuotaExceededError, LLMProviderDisabledError
from app.llm.guarded import QuotaGuardedLLM, reset_llm_request_context, set_llm_request_context
from app.services.llm_quota_service import LLMQuotaService


class FakeRedis:
    def __init__(self, result=1):
        self.result = result
        self.calls = []

    def eval(self, script, numkeys, *args):
        self.calls.append((script, numkeys, args))
        return self.result


class FakeProvider:
    def __init__(self):
        self.calls = 0

    def invoke(self, prompt, config=None, **kwargs):
        self.calls += 1
        return "ok"

    async def ainvoke(self, prompt, config=None, **kwargs):
        self.calls += 1
        return "ok"


def test_estimate_request_tokens_is_positive():
    service = LLMQuotaService(redis_client=FakeRedis())

    estimate = service.estimate_request_tokens("Hello Meowski")

    assert estimate > 0
    assert estimate >= settings.llm_max_output_tokens


def test_reserve_blocks_when_budget_is_exhausted():
    service = LLMQuotaService(redis_client=FakeRedis(result=0))

    with pytest.raises(LLMQuotaExceededError, match="capacity is temporarily exhausted"):
        service.reserve(
            "Hello",
            user_id="user_1",
            session_id="session_1",
        )


def test_reserve_rejects_request_larger_than_per_request_budget(monkeypatch):
    service = LLMQuotaService(redis_client=FakeRedis())
    monkeypatch.setattr(settings, "llm_max_request_tokens", 10)

    with pytest.raises(LLMQuotaExceededError, match="exceeds the application LLM token budget"):
        service.reserve(
            "A" * 1000,
            user_id="user_1",
            session_id="session_1",
        )


def test_provider_disabled_fails_closed(monkeypatch):
    service = LLMQuotaService(redis_client=FakeRedis())
    monkeypatch.setattr(settings, "llm_provider_enabled", False)

    with pytest.raises(LLMProviderDisabledError):
        service.reserve(
            "Hello",
            user_id="user_1",
            session_id="session_1",
        )


def test_guard_reserves_before_provider_call():
    class FakeQuota:
        def __init__(self):
            self.calls = []
            self.concurrency_calls = []
            self.settlements = []

        def reserve(self, prompt, **kwargs):
            self.calls.append((prompt, kwargs))
            return 100

        def acquire_concurrency(self , provider=None):
            self.concurrency_calls.append("acquire")
            return "test-concurrency-key"

        def release_concurrency(self, key):
            self.concurrency_calls.append(("release", key))

        def settle(self, estimated_tokens, actual_tokens):
            self.settlements.append((estimated_tokens, actual_tokens))

    provider = FakeProvider()
    quota = FakeQuota()
    guard = QuotaGuardedLLM(provider, quota)

    token = set_llm_request_context("user_1", "session_1")
    try:
        assert guard.invoke("Hello") == "ok"
    finally:
        reset_llm_request_context(token)

    assert provider.calls == 1
    assert quota.calls[0][0] == "Hello"
    assert quota.calls[0][1]["user_id"] == "user_1"
    assert quota.calls[0][1]["session_id"] == "session_1"


def test_guard_does_not_call_provider_when_quota_blocks():
    class BlockingQuota:
        def reserve(self, prompt, **kwargs):
            raise LLMQuotaExceededError("blocked")

    provider = FakeProvider()
    guard = QuotaGuardedLLM(provider, BlockingQuota())

    token = set_llm_request_context("user_1", "session_1")
    try:
        with pytest.raises(LLMQuotaExceededError):
            guard.invoke("Hello")
    finally:
        reset_llm_request_context(token)

    assert provider.calls == 0


class ConcurrencyRedis:
    def __init__(self, count=0):
        self.count = count

    def incr(self, key):
        self.count += 1
        return self.count

    def decr(self, key):
        self.count -= 1
        return self.count

    def expire(self, key, seconds):
        pass


def test_concurrency_guard_blocks_when_limit_is_reached(monkeypatch):
    service = LLMQuotaService(redis_client=ConcurrencyRedis(count=1))
    monkeypatch.setattr(settings, "llm_concurrency_limit", 1)

    from app.llm.exceptions import LLMConcurrencyLimitError

    with pytest.raises(LLMConcurrencyLimitError, match="capacity is busy"):
        service.acquire_concurrency()


def test_concurrency_guard_releases_after_provider_call():
    class FakeQuota:
        def __init__(self):
            self.released = []
            self.settlements = []

        def reserve(self, prompt, **kwargs):
            return 100

        def acquire_concurrency(self, provider=None):
            return "key"

        def release_concurrency(self, key):
            self.released.append(key)

        def settle(self, estimated_tokens, actual_tokens):
            self.settlements.append((estimated_tokens, actual_tokens))

    provider = FakeProvider()
    quota = FakeQuota()
    guard = QuotaGuardedLLM(provider, quota)

    token = set_llm_request_context("user_1", "session_1")
    try:
        assert guard.invoke("Hello") == "ok"
    finally:
        reset_llm_request_context(token)

    assert quota.released == ["key"]
