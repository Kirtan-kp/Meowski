from app.graph.state import RAGState
from langchain_core.output_parsers import StrOutputParser

def retrieve_node(state : RAGState , retriever) -> dict:

    documents = retriever.invoke(state["question"])

    return {"documents" : documents}

def generate_node(state : RAGState , prompt , llm) -> dict:

    context = "\n\n".join(document.page_content for document in state["documents"])

    answer = (prompt | llm | StrOutputParser()).invoke(
        {
            "context" : context,
            "question" : state["question"]
        }
    )

    return {"context" : context , "answer" : answer}