from typing import TypedDict
from langchain_core.messages import BaseMessage

class RAGState(TypedDict , total = False):

    question: str

    documents: list[dict]

    context: str

    answer: str

    retry_count : int

    rewritten_question : str

    chat_history : list[BaseMessage]

    user_id: str

    session_id: str

    request_id: str

    preferences: list[dict]

    mode: str  # "portfolio" | "document" | "mixed" | "general"