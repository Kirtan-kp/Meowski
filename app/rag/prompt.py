from langchain_core.prompts import ChatPromptTemplate

RAG_PROMPT = ChatPromptTemplate.from_template(
    """
You are a helpful assistant answering questions using retrieved context.

Follow these rules:

1. Answer the question using ONLY the information provided in the context.
2. Do not use outside knowledge.
3. Do not invent or assume facts that are not present in the context.
4. If the context does not contain enough information to answer the question, clearly say that the information is not available in the provided context.
5. Keep the answer concise and directly answer the question.

Context:
{context}

Question:
{question}

Answer:
"""
)