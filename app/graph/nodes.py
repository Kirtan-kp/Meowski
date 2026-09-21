from app.graph.state import RAGState
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from qdrant_client.models import Filter, FieldCondition, MatchValue
from app.rag.context import build_context
from app.services.llm_cache_service import LLMCacheService
import logging
import time
from app.api.dependencies import get_observability_service

logger = logging.getLogger(__name__)

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

    request_id = state.get("request_id" , "unknown")
    start_time = time.perf_counter()

    if state.get("retry_count" , 0) > 0:
        question = state.get("rewritten_question", state["question"])
    else:
        question = state["question"]

    access_filter = Filter(
        should=[
            Filter(
                must=[
                    FieldCondition(
                        key = "metadata.scope",
                        match = MatchValue(value = "portfolio")
                    )
                ]
            ),
            Filter(
                must=[
                    FieldCondition(
                        key = "metadata.scope",
                        match = MatchValue(value = "session")
                    ),
                    FieldCondition(
                        key = "metadata.user_id",
                        match = MatchValue(value = state["user_id"])
                    ),
                    FieldCondition(
                        key = "metadata.session_id",
                        match = MatchValue(value = state["session_id"])
                    )
                ]
            )
        ]
    )

    try:
        documents = retriever.invoke(question , filter = access_filter)
        document_ids = [
            str(
                document.metadata.get(
                    "_id",
                    document.metadata.get(
                        "file_id",
                        "unknown",
                    ),
                )
            )
            for document in documents
        ]

        retrieval_scores = [
            float(
                document.metadata.get(
                    "retrieval_score",
                    document.metadata.get(
                        "score",
                        0,
                    ),
                )
            )
            for document in documents
        ]

        reranker_scores = [
            float(
                document.metadata.get(
                    "relevance_score",
                    0,
                )
            )
            for document in documents
        ]
        process_time = time.perf_counter() - start_time
        observability = get_observability_service()

        observability.record_retrieval(
            document_ids=document_ids,
            retrieval_scores=retrieval_scores,
            reranker_scores=reranker_scores,
            latency_ms=process_time * 1000,
        )

        logger.info(
            "request_id=%s stage=retrieval latency_ms=%.2f documents=%s retry_count=%s",
            request_id , process_time * 1000 , len(documents) , state.get("retry_count", 0))

    except Exception:

        process_time = time.perf_counter() - start_time

        logger.exception("request_id=%s stage=retrieval failed latency_ms=%.2f" , request_id , process_time * 1000)

        raise

    serializable_documents = [
        {
            "page_content" : document.page_content,
            "metadata" : make_serializable(document.metadata)
        }
        for document in documents
    ]

    return {
        "documents" : serializable_documents,
        "retry_count" : state.get("retry_count", 0)
    }

def generate_node(state : RAGState , prompt , llm) -> dict:

    request_id = state.get("request_id", "unknown")
    start_time = time.perf_counter()
    context = build_context(state["documents"])

    if state.get("retry_count", 0) > 0:
        question = state.get("rewritten_question", state["question"])
    else:
        question = state["question"]

    chat_history = state.get("chat_history", [])

    cache = LLMCacheService()

    cached_answer = cache.get(
        question=question,
        context=context,
        chat_history=chat_history,
        user_id=state["user_id"],
        session_id=state["session_id"],
    )

    if cached_answer is not None:
        answer = cached_answer
        process_time = time.perf_counter() - start_time

        logger.info(
            "request_id=%s stage=generation cache_hit=true latency_ms=%.2f",
            request_id,
            process_time * 1000,
        )

    else:

        try:
            answer = (prompt | llm | StrOutputParser()).invoke(
                {
                    "context" : context,
                    "question" : question,
                    "chat_history" : chat_history
                }
            )
            process_time = time.perf_counter() - start_time

            logger.info(
                "request_id=%s stage=generation cache_hit=false latency_ms=%.2f",
                request_id,
                process_time * 1000,
            )
        except Exception:

            process_time = time.perf_counter() - start_time

            logger.exception(
                "request_id=%s stage=generation failed latency_ms=%.2f",
                request_id,
                process_time * 1000,
            )

            raise

        cache.set(
            question=question,
            context=context,
            chat_history=chat_history,
            user_id=state["user_id"],
            session_id=state["session_id"],
            answer=answer
        )
        
    return {"context" : context , "answer" : answer , "documents" : state["documents"] , 
            "chat_history": [HumanMessage(content = state["question"]) , AIMessage(content = answer)]}

def rewrite_query_node(state : RAGState , llm) -> dict: 

    chat_history = state.get("chat_history" , [])

    history_text = "\n".join(f"{message.type} : {message.content}" for message in chat_history)

    rewrite_prompt = ("Rewrite the following question to make it clearer and " 
                      "more useful for retrieving relevant documents.\n\n"
                      f"Conversation history:\n{history_text}\n\n" 
                      f"Original question: {state['question']}\n\n" 
                      "Return only the rewritten question." )

    start_time = time.perf_counter()
    try:
        rewritten_question = llm.invoke(rewrite_prompt) 
        process_time = time.perf_counter() - start_time

        logger.info(
            "request_id=%s stage=query_rewrite latency_ms=%.2f",
            state.get("request_id", "unknown"),
            process_time * 1000,
        )

    except Exception:

        process_time = time.perf_counter() - start_time

        logger.exception(
            "request_id=%s stage=query_rewrite failed latency_ms=%.2f",
            state.get("request_id", "unknown"),
            process_time * 1000,
        )

        raise

    return {"rewritten_question" : rewritten_question.content 
            if hasattr(rewritten_question , "content") 
            else str(rewritten_question), 
            "retry_count" : state.get("retry_count" , 0) + 1}