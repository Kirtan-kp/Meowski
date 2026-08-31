from app.graph.state import RAGState
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage

def make_serializable(value):

    if hasattr(value , "item"):
        return value.item()

    if isinstance(value , dict):
        return {key : make_serializable(item) for key , item in value.items()}

    if isinstance(value , list):
        return [make_serializable(item) for item in value]

    if isinstance(value , tuple):
        return tuple(make_serializable(item) for item in value)

    return value

def retrieve_node(state : RAGState , retriever) -> dict:

    question = state.get("rewritten_question" , state["question"])

    documents = retriever.invoke(question)

    serializable_documents = [
        {
            "page_content": document.page_content,
            "metadata": make_serializable(document.metadata)
        }
        for document in documents
    ]

    return {
        "documents": serializable_documents,
        "retry_count": state.get("retry_count", 0)
    }

def generate_node(state : RAGState , prompt , llm) -> dict:

    context = "\n\n".join(document["page_content"] for document in state["documents"])

    question = state.get("rewritten_question" , state["question"] )

    answer = (prompt | llm | StrOutputParser()).invoke(
        {
            "context" : context,
            "question" : question,
            "chat_history" : state.get("chat_history" , [])
        }
    )

    return {"context" : context , "answer" : answer , "documents" : state["documents"] , 
            "chat_history": [HumanMessage(content = question) , AIMessage(content = answer)]}

def rewrite_query_node(state : RAGState , llm) -> dict: 

    rewrite_prompt = ("Rewrite the following question to make it clearer and " 
                      "more useful for retrieving relevant documents.\n\n" 
                      f"Original question: {state['question']}\n\n" 
                      "Return only the rewritten question." )
     
    rewritten_question = llm.invoke(rewrite_prompt) 

    return {"rewritten_question" : rewritten_question.content 
            if hasattr(rewritten_question , "content") 
            else str(rewritten_question), 
            "retry_count" : state.get("retry_count" , 0) + 1}