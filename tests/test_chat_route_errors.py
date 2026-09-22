from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.routes.chat import router, get_chat_service
from app.llm.exceptions import LLMTimeoutError,LLMRateLimitError,LLMProviderError,LLMQuotaExceededError,LLMProviderDisabledError,LLMConcurrencyLimitError
from app.middleware.request_logging import request_logging_middleware
from app.api.dependencies import get_rate_limit_service

def create_app(error):

    app = FastAPI()
    app.middleware("http")(request_logging_middleware)
    captured_request_ids = []

    class FakeChatService:

        def generate_response(
            self,
            message,
            session_id,
            user_id,
            request_id,
        ):

            captured_request_ids.append(request_id)

            if error:
                raise error

            class Response:
                answer = "Test answer"
                sources = []

            return Response()

    def fake_get_chat_service():
        return FakeChatService()

    app.dependency_overrides[get_chat_service] = fake_get_chat_service

    class AllowAllRateLimits:
        def scoped_key(self, *parts):
            return "test"

        def is_allowed(self, **kwargs):
            return True

    app.dependency_overrides[get_rate_limit_service] = lambda: AllowAllRateLimits()
    app.include_router(router, prefix="/api/v1")

    return app, captured_request_ids


def test_chat_timeout_returns_504():

    app, _ = create_app(
        LLMTimeoutError("LLM provider request timed out")
    )

    client = TestClient(app)

    response = client.post(
        "/api/v1/chat",
        json={
            "message": "Hello",
            "session_id": "session_1",
            "user_id": "user_1",
        },
    )

    assert response.status_code == 504
    assert response.json()["detail"] == "LLM provider request timed out"


def test_chat_rate_limit_returns_429():

    app, _ = create_app(
        LLMRateLimitError("LLM provider rate limit exceeded")
    )

    client = TestClient(app)

    response = client.post(
        "/api/v1/chat",
        json={
            "message": "Hello",
            "session_id": "session_1",
            "user_id": "user_1",
        },
    )

    assert response.status_code == 429
    assert response.json()["detail"] == "LLM provider rate limit exceeded"


def test_chat_provider_error_returns_503():

    app, _ = create_app(
        LLMProviderError("LLM provider request failed")
    )

    client = TestClient(app)

    response = client.post(
        "/api/v1/chat",
        json={
            "message": "Hello",
            "session_id": "session_1",
            "user_id": "user_1",
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "LLM provider request failed"


def test_chat_success_returns_200():

    app, _ = create_app(None)

    client = TestClient(app)

    response = client.post(
        "/api/v1/chat",
        json={
            "message": "Hello",
            "session_id": "session_1",
            "user_id": "user_1",
        },
    )

    assert response.status_code == 200
    assert response.json()["response"] == "Test answer"
    assert response.json()["sources"] == []


def test_chat_passes_request_id():

    app, captured_request_ids = create_app(None)

    client = TestClient(app)

    response = client.post(
        "/api/v1/chat",
        json={
            "message": "Hello",
            "session_id": "session_1",
            "user_id": "user_1",
        },
    )

    assert response.status_code == 200
    assert len(captured_request_ids) == 1
    assert captured_request_ids[0]

def test_chat_quota_exceeded_returns_429():
    app, _ = create_app(LLMQuotaExceededError("LLM capacity is temporarily exhausted. Please try again later."))
    response = TestClient(app).post("/api/v1/chat", json={"message": "Hello", "session_id": "session_1", "user_id": "user_1"})
    assert response.status_code == 429


def test_chat_provider_disabled_returns_503():
    app, _ = create_app(LLMProviderDisabledError("LLM provider is disabled by application policy"))
    response = TestClient(app).post("/api/v1/chat", json={"message": "Hello", "session_id": "session_1", "user_id": "user_1"})
    assert response.status_code == 503


def test_chat_concurrency_limit_returns_429():
    app, _ = create_app(LLMConcurrencyLimitError("LLM capacity is busy. Please try again shortly."))
    response = TestClient(app).post("/api/v1/chat", json={"message": "Hello", "session_id": "session_1", "user_id": "user_1"})
    assert response.status_code == 429