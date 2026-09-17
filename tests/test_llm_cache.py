from langchain_core.messages import HumanMessage, AIMessage

from app.services.llm_cache_service import LLMCacheService


class FakeCache:

    def __init__(self):
        self.data = {}
        self.set_calls = 0

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value, ttl_seconds):
        self.data[key] = value
        self.set_calls += 1

    def delete(self, key):
        self.data.pop(key, None)


def test_llm_cache_hit():
    service = LLMCacheService()
    service.cache = FakeCache()

    history = [
        HumanMessage(content="Hello"),
        AIMessage(content="Hi"),
    ]

    service.set(
        question="What is Meowski?",
        context="Meowski is a RAG chatbot.",
        chat_history=history,
        user_id="user_1",
        session_id="session_1",
        answer="Meowski is a RAG chatbot.",
    )

    result = service.get(
        question="What is Meowski?",
        context="Meowski is a RAG chatbot.",
        chat_history=history,
        user_id="user_1",
        session_id="session_1",
    )

    assert result == "Meowski is a RAG chatbot."
    assert service.cache.set_calls == 1


def test_different_sessions_do_not_share_llm_cache():
    service = LLMCacheService()
    service.cache = FakeCache()

    service.set(
        question="What is my project?",
        context="Private project A.",
        chat_history=[],
        user_id="user_1",
        session_id="session_1",
        answer="Project A.",
    )

    result = service.get(
        question="What is my project?",
        context="Private project A.",
        chat_history=[],
        user_id="user_1",
        session_id="session_2",
    )

    assert result is None


def test_different_users_do_not_share_llm_cache():
    service = LLMCacheService()
    service.cache = FakeCache()

    service.set(
        question="What is my project?",
        context="Private project.",
        chat_history=[],
        user_id="user_1",
        session_id="session_1",
        answer="Private answer.",
    )

    result = service.get(
        question="What is my project?",
        context="Private project.",
        chat_history=[],
        user_id="user_2",
        session_id="session_1",
    )

    assert result is None


def test_different_contexts_do_not_share_llm_cache():
    service = LLMCacheService()
    service.cache = FakeCache()

    service.set(
        question="What is my project?",
        context="Project A.",
        chat_history=[],
        user_id="user_1",
        session_id="session_1",
        answer="Answer A.",
    )

    result = service.get(
        question="What is my project?",
        context="Project B.",
        chat_history=[],
        user_id="user_1",
        session_id="session_1",
    )

    assert result is None


def test_different_chat_history_does_not_share_llm_cache():
    service = LLMCacheService()
    service.cache = FakeCache()

    history_one = [
        HumanMessage(content="Tell me about Python."),
        AIMessage(content="Python is a programming language."),
    ]

    history_two = [
        HumanMessage(content="Tell me about RAG."),
        AIMessage(content="RAG retrieves relevant context."),
    ]

    service.set(
        question="Tell me more.",
        context="Some context.",
        chat_history=history_one,
        user_id="user_1",
        session_id="session_1",
        answer="Python answer.",
    )

    result = service.get(
        question="Tell me more.",
        context="Some context.",
        chat_history=history_two,
        user_id="user_1",
        session_id="session_1",
    )

    assert result is None