import pytest

from app.llm.exceptions import (
    LLMProviderError,
    LLMTimeoutError,
)
from app.services.chat_service import ChatService

class FakePreferenceService:

    def get_preferences(self, user_id):
        return []

class FakeChatService:

    def __init__(self):
        self.request_id = None

    def generate_response(
        self,
        message,
        session_id,
        user_id,
        request_id,
    ):
        self.request_id = request_id

        class Response:
            answer = "Test answer"
            sources = []

        return Response()

class FakeSessionService:

    def get_state(self, session_id, user_id):
        return None

    def save_state(self, session_id, user_id, state):
        pass


class FakeGraph:

    def __init__(self, error):
        self.error = error

    def invoke(self, state, config):

        if self.error:
            raise self.error

        return {
            "answer": "Test answer",
            "documents": [],
            "chat_history": [],
        }


def create_service(error):

    service = ChatService.__new__(ChatService)

    service.vector_store = None
    service.llm = None
    service.retriever = None
    service.rag_graph = FakeGraph(error)
    service.session_service = FakeSessionService()
    service.preference_service = FakePreferenceService()

    return service


def test_chat_service_preserves_llm_error():

    service = create_service(
        LLMTimeoutError("timeout")
    )

    with pytest.raises(LLMTimeoutError):
        service.generate_response(
            message="Hello",
            session_id="session_1",
            user_id="user_1",
            request_id="test-request-id"
        )


def test_chat_service_normalizes_unexpected_error():

    service = create_service(
        Exception("provider internals")
    )

    with pytest.raises(LLMProviderError, match="LLM provider request failed"):
        service.generate_response(
            message="Hello",
            session_id="session_1",
            user_id="user_1",
            request_id="test-request-id"
        )


def test_chat_service_success_is_unchanged():

    service = create_service(None)

    response = service.generate_response(
        message="Hello",
        session_id="session_1",
        user_id="user_1",
        request_id="test-request-id"
    )

    assert response.answer == "Test answer"
    assert response.sources == []