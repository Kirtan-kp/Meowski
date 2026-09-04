from typing import TypedDict , Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages  #add operator , only to add new messages and not replace

class RAGState(TypedDict , total = False):

    question: str

    documents: list[dict]

    context: str

    answer: str

    retry_count : int

    rewritten_question : str

    chat_history : Annotated[list[BaseMessage] , add_messages]

    user_id: str

    session_id: str