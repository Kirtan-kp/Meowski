from typing import TypedDict
from langchain_core.documents import Document

class RAGState(TypedDict , total = False):

    question: str

    documents: list[Document]

    context: str

    answer: str

    retry_count : int

    rewritten_question : str