from langgraph.graph import StateGraph, START, END
from app.graph.state import RAGState
from app.graph.nodes import retrieve_node, generate_node, generate_general_node, rewrite_query_node
from app.graph.routing import route_after_retrieve
from app.rag.prompt import GENERAL_PROMPT
import logging

logger = logging.getLogger(__name__)

# Kept under the old name so existing imports keep working.
should_retry = route_after_retrieve


def create_rag_graph(retriever, prompt, llm, general_prompt=GENERAL_PROMPT):
    """retrieve -> (generate | rewrite -> retrieve | general)

    - generate: grounded answer from the portfolio or the visitor's uploaded files
    - rewrite:  one retry for follow-up questions that need their context spelled out
    - general:  nothing relevant found, so answer from general knowledge (marked mode="general")
    """
    graph = StateGraph(RAGState)

    graph.add_node("retrieve", lambda state: retrieve_node(state, retriever))
    graph.add_node("rewrite", lambda state: rewrite_query_node(state, llm))
    graph.add_node("generate", lambda state: generate_node(state, prompt, llm))
    graph.add_node("general", lambda state: generate_general_node(state, general_prompt, llm))
    graph.add_edge(START, "retrieve")
    graph.add_conditional_edges("retrieve", route_after_retrieve, {"rewrite": "rewrite", "generate": "generate", "general": "general"})
    graph.add_edge("rewrite", "retrieve")
    graph.add_edge("generate", END)
    graph.add_edge("general", END)

    return graph.compile()