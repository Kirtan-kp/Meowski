from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage
from app.llm.base import BaseLLM
from app.services.chat_service import ChatService

class FakeSessionService:

    def __init__(self):
        self.states = {}

    def get_state(self, session_id, user_id):
        return self.states.get(session_id)

    def save_state(self, session_id, user_id, state):
        self.states[session_id] = state


class FakeGraph:

    def __init__(self):
        self.calls = []

    def invoke(self, state, config):
        self.calls.append((state, config))

        question = state["question"]

        answer = f"Answer to: {question}"

        return {
            "answer": answer,
            "documents": [
                {
                    "page_content": "Test context",
                    "metadata": {
                        "file_id": "file_1",
                        "scope": "portfolio"
                    }
                }
            ],
            "chat_history": [
                *state.get("chat_history", []),
                HumanMessage(content=question),
                AIMessage(content=answer),
            ],
        }


def create_chat_service():
    session_service = FakeSessionService()

    service = ChatService.__new__(ChatService)

    service.vector_store = None
    service.llm = None
    service.retriever = None
    service.rag_graph = FakeGraph()
    service.session_service = session_service

    return service


def test_chat_service_preserves_conversation_history():

    service = create_chat_service()

    first_response = service.generate_response(
        message="What is my first question?",
        session_id="session_1",
        user_id="user_1",
        request_id="test-request-id"
    )

    assert first_response.answer == "Answer to: What is my first question?"

    state = service.session_service.get_state(
        session_id="session_1",
        user_id="user_1",
    )

    assert state["chat_history"] == [
        {
            "role": "user",
            "content": "What is my first question?",
        },
        {
            "role": "assistant",
            "content": "Answer to: What is my first question?",
        },
    ]

    second_response = service.generate_response(
        message="What is my second question?",
        session_id="session_1",
        user_id="user_1",
        request_id="test-request-id"
    )

    assert second_response.answer == "Answer to: What is my second question?"

    graph_calls = service.rag_graph.calls

    second_call_state = graph_calls[1][0]

    assert second_call_state["chat_history"] == [
        HumanMessage(content="What is my first question?"),
        AIMessage(content="Answer to: What is my first question?"),
    ]

    state = service.session_service.get_state(
        session_id="session_1",
        user_id="user_1",
    )

    assert state["chat_history"] == [
        {
            "role": "user",
            "content": "What is my first question?",
        },
        {
            "role": "assistant",
            "content": "Answer to: What is my first question?",
        },
        {
            "role": "user",
            "content": "What is my second question?",
        },
        {
            "role": "assistant",
            "content": "Answer to: What is my second question?",
        },
    ]


def test_chat_service_passes_user_and_session_to_graph():

    service = create_chat_service()

    service.generate_response(
        message="Hello",
        session_id="session_123",
        user_id="user_123",
        request_id="test-request-id"
    )

    state, config = service.rag_graph.calls[0]

    assert state["user_id"] == "user_123"
    assert state["session_id"] == "session_123"

    assert config["configurable"]["thread_id"] == "user_123:session_123"

def test_chat_service_uses_llm_factory(monkeypatch):

    class FakeLLM(BaseLLM):

        @property
        def llm(self):
            return "fake_langchain_llm"

        async def generate(self, prompt: str) -> str:
            return "fake response"

    fake_llm = FakeLLM()

    def fake_create_llm():
        return fake_llm

    def fake_create_retrieval_pipeline(**kwargs):
        assert kwargs["llm"] == "fake_langchain_llm"
        return "fake_retriever"

    def fake_create_rag_graph(**kwargs):
        assert kwargs["retriever"] == "fake_retriever"
        assert kwargs["llm"] == "fake_langchain_llm"
        return "fake_graph"

    monkeypatch.setattr(
        "app.services.chat_service.create_llm",
        fake_create_llm,
    )

    monkeypatch.setattr(
        "app.services.chat_service.create_retrieval_pipeline",
        fake_create_retrieval_pipeline,
    )

    monkeypatch.setattr(
        "app.services.chat_service.create_rag_graph",
        fake_create_rag_graph,
    )

    session_service = FakeSessionService()

    service = ChatService(
        vector_store="fake_vector_store",
        session_service=session_service,
        bm25_index_service=None
    )

    assert service.llm is fake_llm
    assert service.retriever == "fake_retriever"
    assert service.rag_graph == "fake_graph"

def test_chat_service_passes_request_id_to_graph():

    captured_state = {}

    class FakeGraph:

        def invoke(self, state, config):

            captured_state.update(state)

            return {
                "answer": "Test answer",
                "documents": [],
                "chat_history": [],
            }

    service = ChatService.__new__(ChatService)

    service.rag_graph = FakeGraph()
    service.session_service = FakeSessionService()

    service.generate_response(
        message="Hello",
        session_id="session_1",
        user_id="user_1",
        request_id="request_123",
    )

    assert captured_state["request_id"] == "request_123"