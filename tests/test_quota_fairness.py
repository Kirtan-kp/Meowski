import sys
import types
from unittest.mock import MagicMock

import fakeredis
import pytest

from app.core.config import settings
from app.llm.exceptions import LLMQuotaExceededError
from app.services.llm_quota_service import LLMQuotaService


@pytest.fixture(autouse=True)
def stub_dependencies(monkeypatch):
    stub = types.ModuleType("app.api.dependencies")
    stub.get_observability_service = lambda: MagicMock()
    monkeypatch.setitem(sys.modules, "app.api.dependencies", stub)


@pytest.fixture
def service():
    return LLMQuotaService(redis_client=fakeredis.FakeRedis(decode_responses=True))


def reserve(service, session):
    return service.reserve("Hello Meowski", user_id="user", session_id=session)


def test_one_visitor_cannot_use_up_the_shared_window(service, monkeypatch):
    monkeypatch.setattr(settings, "llm_rolling_token_budget", 100000)
    monkeypatch.setattr(settings, "llm_daily_token_budget", 100000)
    monkeypatch.setattr(settings, "llm_provider_daily_token_budget", 100000)
    monkeypatch.setattr(settings, "llm_session_daily_token_budget", 100000)
    monkeypatch.setattr(settings, "llm_session_rolling_token_budget", 2000)

    with pytest.raises(LLMQuotaExceededError) as blocked:
        for _ in range(20):
            reserve(service, "greedy")
    assert 1 <= blocked.value.retry_after <= settings.llm_rolling_window_seconds
    assert reserve(service, "someone-else") > 0  # other visitors are unaffected


def test_global_rolling_budget_still_applies(service, monkeypatch):
    monkeypatch.setattr(settings, "llm_session_rolling_token_budget", 100000)
    monkeypatch.setattr(settings, "llm_session_daily_token_budget", 100000)
    monkeypatch.setattr(settings, "llm_daily_token_budget", 100000)
    monkeypatch.setattr(settings, "llm_provider_daily_token_budget", 100000)
    monkeypatch.setattr(settings, "llm_rolling_token_budget", 2000)

    with pytest.raises(LLMQuotaExceededError, match="temporarily exhausted") as blocked:
        for i in range(20):
            reserve(service, f"session-{i}")
    assert blocked.value.retry_after is not None


def test_daily_limit_reports_time_until_midnight(service, monkeypatch):
    monkeypatch.setattr(settings, "llm_daily_token_budget", 100)  # smaller than one request
    with pytest.raises(LLMQuotaExceededError) as blocked:
        reserve(service, "s")
    assert 1 <= blocked.value.retry_after <= 86400


def test_legacy_integer_results_still_work():
    class Legacy:
        def eval(self, *args):
            return 0

    with pytest.raises(LLMQuotaExceededError, match="temporarily exhausted") as blocked:
        LLMQuotaService(redis_client=Legacy()).reserve("Hello", user_id="u", session_id="s")
    assert blocked.value.retry_after is None
