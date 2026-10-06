from langchain_core.messages import AIMessage, HumanMessage

from app.core.config import settings
from app.graph.routing import refers_to_uploaded_file, is_shareable, looks_like_followup, mode_from_documents, route_after_retrieve, trim_history


def doc(score, scope="portfolio"):
    return {"page_content": "x", "metadata": {"relevance_score": score, "scope": scope}}


def test_relevant_documents_go_to_grounded_answer():
    assert route_after_retrieve({"documents": [doc(0.9)], "question": "Who is Kirtan?"}) == "generate"


def test_unrelated_first_question_skips_rewrite_and_goes_general():
    state = {"documents": [doc(0.1)], "question": "What is the capital of France?", "chat_history": []}
    assert route_after_retrieve(state) == "general"


def test_no_documents_goes_general():
    assert route_after_retrieve({"documents": [], "question": "Tell me a joke", "chat_history": []}) == "general"


def test_follow_up_is_rewritten_once_then_goes_general():
    history = [HumanMessage(content="Tell me about Cat RAG"), AIMessage(content="It is a RAG app.")]
    state = {"documents": [doc(0.1)], "question": "and how does it rank?", "chat_history": history, "retry_count": 0}
    assert route_after_retrieve(state) == "rewrite"
    assert route_after_retrieve({**state, "retry_count": 1}) == "general"


def test_general_answers_disabled_keeps_original_behaviour(monkeypatch):
    monkeypatch.setattr(settings, "general_answers_enabled", False)
    state = {"documents": [doc(0.1)], "question": "Capital of France?", "chat_history": [], "retry_count": 0}
    assert route_after_retrieve(state) == "rewrite"
    assert route_after_retrieve({**state, "retry_count": 1}) == "generate"


def test_followup_detection():
    history = [HumanMessage(content="hi")]
    assert not looks_like_followup("What is the MLOps pipeline built with and why?", [])
    assert looks_like_followup("what about it?", history)
    assert not looks_like_followup("Explain how gradient boosting handles missing values in detail", history)


def test_mode_from_documents():
    assert mode_from_documents([doc(1, "portfolio")]) == "portfolio"
    assert mode_from_documents([doc(1, "session")]) == "document"
    assert mode_from_documents([doc(1, "session"), doc(1, "portfolio")]) == "mixed"


def test_trim_history_keeps_recent_messages_and_clips_long_ones(monkeypatch):
    monkeypatch.setattr(settings, "prompt_history_messages", 2)
    monkeypatch.setattr(settings, "prompt_history_chars", 10)
    history = [HumanMessage(content="old"), AIMessage(content="a" * 50), HumanMessage(content="short")]
    trimmed = trim_history(history)
    assert [m.content for m in trimmed] == ["a" * 10 + "…", "short"]
    assert isinstance(trimmed[0], AIMessage)


def test_shared_cache_only_for_first_public_questions():
    assert is_shareable([], [], "portfolio")
    assert is_shareable([], [], "general")
    assert not is_shareable([HumanMessage(content="hi")], [], "portfolio")
    assert not is_shareable([], [{"key": "tone", "value": "formal"}], "portfolio")
    assert not is_shareable([], [], "document")  # uploaded files are private
    assert not is_shareable([], [], "mixed")


def test_file_questions_are_recognised():
    for q in ["can you tell me about this story like a short summary?", "from the file i uploaded", "Summarize my PDF", "what does the document say"]:
        assert refers_to_uploaded_file(q), q
    for q in ["Who is Kirtan?", "Summarize Kirtan's projects", "What is the capital of France?"]:
        assert not refers_to_uploaded_file(q), q


def test_file_focus_answers_from_the_file_even_with_low_scores():
    state = {"documents": [doc(0.1, "session")], "question": "from the file i uploaded", "file_focus": True, "chat_history": []}
    assert route_after_retrieve(state) == "generate"
    assert route_after_retrieve({**state, "file_focus": False}) == "general"
