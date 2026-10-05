"""Pure helpers that decide how a question is answered and keep prompts small.

Kept free of heavy imports so they are cheap to unit-test."""
import re

from langchain_core.messages import BaseMessage

from app.core.config import settings

_REFERENCE_WORDS = re.compile(r"\b(it|its|this|that|these|those|they|them|their|he|him|his|she|her|there|one)\b", re.IGNORECASE)


def max_relevance(documents: list[dict]) -> float:
    scores = [float((d.get("metadata") or {}).get("relevance_score", 0)) for d in documents]
    return max(scores, default=0.0)


def looks_like_followup(question: str, chat_history: list[BaseMessage]) -> bool:
    """A follow-up leans on earlier turns ("and the second one?"), so a query rewrite can help.
    A self-contained question with no history gains nothing from a rewrite, which would cost another LLM call."""
    if not chat_history:
        return False
    return len(question.split()) <= 6 or bool(_REFERENCE_WORDS.search(question))


def route_after_retrieve(state: dict) -> str:
    """Decide the next graph step: "generate" (grounded answer), "rewrite" (retry retrieval) or "general"."""
    documents = state.get("documents", [])
    retry_count = state.get("retry_count", 0)

    if documents and max_relevance(documents) >= settings.min_relevance_score:
        return "generate"

    if not settings.general_answers_enabled:  # original behaviour: one rewrite, then a grounded (refusing) answer
        return "generate" if retry_count >= 1 else "rewrite"

    if retry_count >= 1:
        return "general"
    if looks_like_followup(state.get("question", ""), state.get("chat_history", [])):
        return "rewrite"
    return "general"


def trim_history(chat_history: list[BaseMessage]) -> list[BaseMessage]:
    """Last few messages only, each clipped, so long conversations do not inflate every prompt."""
    recent = list(chat_history)[-settings.prompt_history_messages:]
    clipped = []
    for message in recent:
        text = message.content if isinstance(message.content, str) else str(message.content)
        if len(text) > settings.prompt_history_chars:
            message = type(message)(content=text[: settings.prompt_history_chars] + "…")
        clipped.append(message)
    return clipped


def mode_from_documents(documents: list[dict]) -> str:
    """"portfolio", "document" (uploaded file) or "mixed", based on the scope Meowski stamps on each chunk."""
    scopes = {(d.get("metadata") or {}).get("scope", "portfolio") for d in documents}
    has_doc, has_portfolio = "session" in scopes, bool(scopes - {"session"})
    if has_doc and has_portfolio:
        return "mixed"
    return "document" if has_doc else "portfolio"


def is_shareable(chat_history: list[BaseMessage], preferences: list[dict], mode: str) -> bool:
    """A first question about public portfolio content has the same answer for every visitor, so it can share one cache entry."""
    return settings.shared_answer_cache_enabled and not chat_history and not preferences and mode in ("portfolio", "general")
