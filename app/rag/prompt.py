from langchain_core.prompts import ChatPromptTemplate , MessagesPlaceholder

RAG_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are a helpful assistant.

Answer the user's question using ONLY the provided context.

If the answer cannot be found in the context, say:
"The information is not available in the provided context."

Do not make up information.

Conversation history may be used to understand references in the user's question, but factual answers must still come from the provided context.

Context:
{context}
"""
        ) , MessagesPlaceholder(variable_name = "chat_history") , ("human" , "{question}")
    ]
)