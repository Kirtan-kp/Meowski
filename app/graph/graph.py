from langgraph.graph import StateGraph, START, END
from app.graph.state import RAGState
from app.graph.nodes import retrieve_node, generate_node

def create_rag_graph(retriever , prompt , llm):

    graph = StateGraph(RAGState)

    graph.add_node("retrieve" , lambda state : retrieve_node(state , retriever))
    graph.add_node("generate" , lambda state: generate_node(state , prompt , llm))
    graph.add_edge(START , "retrieve")
    graph.add_edge("retrieve" , "generate")
    graph.add_edge("generate" , END)

    return graph.compile()