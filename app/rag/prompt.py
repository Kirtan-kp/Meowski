from langchain_core.prompts import ChatPromptTemplate

RAG_PROMPT = ChatPromptTemplate.from_template(
    """
You are a helpful AI assistant.

Answer the user's question using only the provided context.

If the answer cannot be found in the context, say that you don't have enough information.

Context:
{context}

Question:
{question}

Answer:
"""
)