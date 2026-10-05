import sys
import types
from unittest.mock import MagicMock

import fakeredis
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import settings
from app.services.llm_quota_service import LLMQuotaService


@pytest.fixture(autouse=True)
def stub_dependencies(monkeypatch):
    stub = types.ModuleType("app.api.dependencies")
    stub.get_observability_service = lambda: MagicMock()
    stub.get_llm_quota_service = lambda: None  # replaced through dependency_overrides below
    monkeypatch.setitem(sys.modules, "app.api.dependencies", stub)
    monkeypatch.setattr(settings, "llm_daily_token_budget", 100000)
    monkeypatch.setattr(settings, "llm_provider_daily_token_budget", 100000)
    monkeypatch.setattr(settings, "llm_session_daily_token_budget", 100000)
    monkeypatch.setattr(settings, "llm_rolling_token_budget", 100000)
    monkeypatch.setattr(settings, "llm_session_rolling_token_budget", 8000)


@pytest.fixture
def service():
    return LLMQuotaService(redis_client=fakeredis.FakeRedis(decode_responses=True))


def test_fresh_visitor_has_a_full_meter(service):
    usage = service.get_usage("u", "s")
    assert usage["fraction"] == 1.0 and usage["limited_by"] == "session_hourly" and usage["resets_in"] is None
    assert usage["questions_left"] == 8000 // settings.usage_default_question_tokens


def test_meter_drops_as_questions_are_asked_and_empties(service):
    cost = service.reserve("Hello Meowski", user_id="u", session_id="s")
    after = service.get_usage("u", "s")
    assert after["fraction"] < 1.0
    assert after["questions_left"] == (8000 - cost) // cost  # uses the visitor's own average cost

    while service.get_usage("u", "s")["questions_left"] > 0:
        service.reserve("Hello Meowski", user_id="u", session_id="s")
    empty = service.get_usage("u", "s")
    assert empty["questions_left"] == 0 and 1 <= empty["resets_in"] <= settings.llm_rolling_window_seconds


def test_other_visitors_are_not_affected(service):
    for _ in range(3):
        service.reserve("Hello Meowski", user_id="u", session_id="busy")
    assert service.get_usage("u", "fresh")["fraction"] == 1.0


def test_usage_endpoint(service, monkeypatch):
    from app.api.routes import usage as usage_route

    app = FastAPI()
    app.include_router(usage_route.router, prefix="/api/v1")
    app.dependency_overrides[usage_route.get_llm_quota_service] = lambda: service
    client = TestClient(app)

    body = client.get("/api/v1/usage", params={"user_id": "u", "session_id": "s"}).json()
    assert set(body) == {"questions_left", "fraction", "resets_in", "limited_by"}
    assert client.get("/api/v1/usage", params={"user_id": "u"}).status_code == 422
