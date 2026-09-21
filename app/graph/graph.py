from langgraph.graph import StateGraph, START, END
from app.graph.state import RAGState
from app.graph.nodes import retrieve_node, generate_node, rewrite_query_node 
from langgraph.checkpoint.memory import MemorySaver
import logging

logger = logging.getLogger(__name__)

def should_retry(state: RAGState) -> str: 

    retry_count = state.get("retry_count", 0)
    if retry_count >= 1:
        return "generate"
    
    documents = state.get("documents" , []) 

    if not documents: 
        return "rewrite"

    scores = [float(document["metadata"].get("relevance_score" , 0)) for document in documents]
    max_score = max(scores , default = 0)

    if max_score < 0.5:
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

    checkpointer = MemorySaver()

    return graph.compile(checkpointer = checkpointer)