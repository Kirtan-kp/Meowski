import sys
import types
from unittest.mock import MagicMock

import pytest
from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda

from app.rag.prompt import RAG_PROMPT


class FakeCacheService:
    store = {}

    def get(self, **kwargs):
        return self.store.get((kwargs["question"], kwargs["context"], kwargs["user_id"]))

    def set(self, **kwargs):
        self.store[(kwargs["question"], kwargs["context"], kwargs["user_id"])] = kwargs["answer"]


class FakeRetriever:
    def __init__(self, documents):
        self.documents = documents

    def invoke(self, question, filter=None):
        return self.documents


class CountingLLM:
    """Plays the model: records every prompt it receives."""

    def __init__(self):
        self.prompts = []

    def runnable(self):
        def respond(prompt):
            self.prompts.append(prompt)
            text = prompt if isinstance(prompt, str) else " ".join(m.content for m in prompt.to_messages())
            return "REWRITTEN" if "Rewrite the following question" in text else "ANSWER"
        return RunnableLambda(respond)


@pytest.fixture
def graph_env(monkeypatch):
    stub = types.ModuleType("app.api.dependencies")
    stub.get_observability_service = lambda: MagicMock()
    monkeypatch.setitem(sys.modules, "app.api.dependencies", stub)
    for name in ("app.graph.nodes", "app.graph.graph"):
        sys.modules.pop(name, None)
    import app.graph.graph as graph
    import app.graph.nodes as nodes

    FakeCacheService.store = {}
    monkeypatch.setattr(nodes, "LLMCacheService", FakeCacheService)
    yield graph
    for name in ("app.graph.nodes", "app.graph.graph"):
        sys.modules.pop(name, None)


def run(graph_module, documents, question, history=None):
    llm = CountingLLM()
    compiled = graph_module.create_rag_graph(FakeRetriever(documents), RAG_PROMPT, llm.runnable())
    state = {"question": question, "user_id": "u", "session_id": "s", "request_id": "r", "retry_count": 0,
             "chat_history": history or [], "preferences": []}
    return compiled.invoke(state), llm


def chunk(score, scope="portfolio"):
    return Document(page_content="Kirtan built Cat RAG.", metadata={"relevance_score": score, "scope": scope, "source_filename": "portfolio.txt"})


def test_relevant_question_is_grounded_and_marked_portfolio(graph_env):
    result, llm = run(graph_env, [chunk(0.9)], "Who is Kirtan?")
    assert result["mode"] == "portfolio" and result["documents"] and len(llm.prompts) == 1


def test_uploaded_file_answer_is_marked_document(graph_env):
    result, _ = run(graph_env, [chunk(0.9, "session")], "Summarize my file")
    assert result["mode"] == "document"


def test_unrelated_question_gets_a_general_answer_with_one_llm_call(graph_env):
    result, llm = run(graph_env, [chunk(0.05)], "What is the capital of France?")
    assert result["mode"] == "general" and result["documents"] == [] and result["answer"] == "ANSWER"
    assert len(llm.prompts) == 1  # no rewrite call was spent


def test_general_answers_are_shared_between_visitors(graph_env):
    run(graph_env, [chunk(0.05)], "What is the capital of France?")
    _, llm = run(graph_env, [chunk(0.05)], "What is the capital of France?")
    assert llm.prompts == []  # second visitor is served from the shared cache


def test_follow_up_is_rewritten_before_falling_back(graph_env):
    from langchain_core.messages import AIMessage, HumanMessage

    history = [HumanMessage(content="Tell me about Cat RAG"), AIMessage(content="A RAG app.")]
    result, llm = run(graph_env, [chunk(0.05)], "and how does it rank?", history)
    assert len(llm.prompts) == 2 and result["mode"] == "general"
    assert len(result["chat_history"]) == 4
