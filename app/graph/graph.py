from langgraph.graph import StateGraph, START, END
from app.graph.state import RAGState
from app.graph.nodes import retrieve_node, generate_node, rewrite_query_node 

def should_retry(state: RAGState) -> str: 

    documents = state.get("documents" , []) 

    if not documents and state.get("retry_count" , 0) < 1: 
        return "rewrite" 
    
    return "generate"

def create_rag_graph(retriever , prompt , llm):

    graph = StateGraph(RAGState)

    graph.add_node("retrieve" , lambda state : retrieve_node(state , retriever))
    graph.add_node("rewrite", lambda state: rewrite_query_node(state, llm))
    graph.add_node("generate" , lambda state: generate_node(state , prompt , llm))
    graph.add_edge(START , "retrieve")
    graph.add_conditional_edges("retrieve" , should_retry , {"rewrite" : "rewrite", "generate" : "generate"})
    graph.add_edge( "rewrite", "retrieve" )
    graph.add_edge("generate" , END)

    return graph.compile()