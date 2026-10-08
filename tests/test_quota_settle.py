import sys
import types
from types import SimpleNamespace
from unittest.mock import MagicMock

import fakeredis
import pytest

from app.core.config import settings
from app.llm.exceptions import LLMProviderError
from app.services.llm_quota_service import LLMQuotaService, Reservation


@pytest.fixture(autouse=True)
def stub_dependencies(monkeypatch):
    stub = types.ModuleType("app.api.dependencies")
    stub.get_observability_service = lambda: MagicMock()
    monkeypatch.setitem(sys.modules, "app.api.dependencies", stub)
    monkeypatch.setattr(settings, "llm_session_rolling_token_budget", 10000)
    monkeypatch.setattr(settings, "llm_rolling_token_budget", 100000)


@pytest.fixture
def service():
    return LLMQuotaService(redis_client=fakeredis.FakeRedis(decode_responses=True))


def counters(service, reservation):
    daily, provider, session, rolling, session_rolling = reservation.keys
    r = service.redis
    window = lambda key: sum(int(m.rsplit("|", 1)[1]) for m in r.zrange(key, 0, -1))
    return int(r.get(daily)), int(r.get(provider)), int(r.get(session)), window(rolling), window(session_rolling)


def test_reservation_behaves_like_an_int(service):
    reserved = service.reserve("Hello", user_id="u", session_id="s")
    assert isinstance(reserved, Reservation) and reserved > 0 and reserved + 1 == int(reserved) + 1


def test_settle_replaces_the_estimate_with_real_usage(service):
    reserved = service.reserve("Hello", user_id="u", session_id="s")
    assert counters(service, reserved) == (reserved,) * 5
    service.settle(reserved, 300)
    assert counters(service, reserved) == (300,) * 5


def test_settle_can_also_charge_more_and_ignores_unknown_usage(service):
    reserved = service.reserve("Hello", user_id="u", session_id="s")
    service.settle(reserved, None)
    assert counters(service, reserved) == (reserved,) * 5
    service.settle(reserved, int(reserved) + 50)
    assert counters(service, reserved) == (int(reserved) + 50,) * 5


def test_failed_calls_are_given_back_and_counters_never_go_negative(service):
    reserved = service.reserve("Hello", user_id="u", session_id="s")
    service.settle(reserved, 0)
    assert counters(service, reserved) == (1,) * 5
    other = service.reserve("Hello", user_id="u", session_id="s2")
    service.redis.set(other.keys[0], 0)  # simulate counters that were reset (e.g. expired) before settling
    service.settle(other, 5000)
    assert int(service.redis.get(other.keys[0])) >= 0


def test_more_questions_fit_after_settling(service):
    asked = 0
    while True:
        try:
            service.settle(service.reserve("Hello Meowski", user_id="u", session_id="s"), 400)
        except Exception:
            break
        asked += 1
        assert asked < 100
    # Without settling, each question would stay charged at its ~927-token estimate (10 questions per 10,000 tokens).
    assert asked >= 2 * (10000 // 927)


def test_guarded_llm_settles_after_success_and_after_failure(service):
    from app.llm.guarded import QuotaGuardedLLM, reset_llm_request_context, set_llm_request_context

    class Ok:
        def invoke(self, input, config=None, **kwargs):
            return SimpleNamespace(usage_metadata={"input_tokens": 100, "output_tokens": 50, "total_tokens": 150}, content="hi")

    class Boom:
        def invoke(self, input, config=None, **kwargs):
            raise RuntimeError("429 rate limit")

    token = set_llm_request_context("u", "s")
    try:
        QuotaGuardedLLM(Ok(), service, provider_name="groq", model="m").invoke("Hello")
        usage = service.get_usage("u", "s")
        assert usage["fraction"] == round((10000 - 150) / 10000, 3)
        with pytest.raises(Exception):
            QuotaGuardedLLM(Boom(), service, provider_name="groq", model="m").invoke("Hello again")
        assert service.get_usage("u", "s")["fraction"] >= round((10000 - 151) / 10000, 3) - 0.001
    finally:
        reset_llm_request_context(token)
