from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

def create_rag_chain(retriever , llm , prompt):

    def run_rag(question):

        documents = retriever.invoke(question)

        if not documents:                      #if no documents are there we can keep away llm from generating its own answer

            return {
                "answer": (
                    "I don't have enough information "
                    "in the provided context to answer that question."
                ),
                "documents": []
            }

        context = "\n\n".join(document.page_content for document in documents)

        answer = (prompt | llm | StrOutputParser()).invoke({"context" : context , "question" : question , "chat_history" : []})

        serializable_documents = [
            {
                "page_content": document.page_content,
                "metadata": document.metadata
            }
            for document in documents
        ]

        return {"answer" : answer , "documents" : serializable_documents}

    return RunnableLambda(run_rag)