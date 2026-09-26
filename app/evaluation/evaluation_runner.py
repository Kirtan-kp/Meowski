import time
from app.llm.exceptions import LLMQuotaExceededError
from app.evaluation.citation_metrics import (
    calculate_citation_presence,
    calculate_citation_validity,
    calculate_expected_citation_recall
)

from app.evaluation.generation_metrics import (
    calculate_keyword_correctness
)


def evaluate_generation_case(
    question: str,
    reference_answer: str,
    expected_citations: list[int],
    rag_graph,
    evaluator_llm,
    user_id: str,
    session_id: str,
):
    start_time = time.perf_counter()

    try:
        result = rag_graph.invoke(
            {
                "question": question,
                "user_id": user_id,
                "session_id": session_id,
                "request_id": f"evaluation-{time.time_ns()}",
                "retry_count": 0,
                "chat_history": [],
                "preferences": [],
            },
            config={
                "configurable": {
                    "thread_id": f"{user_id}:{session_id}"
                }
            },
        )
    except LLMQuotaExceededError as exc:
        return {
            "status": "quota_blocked",
            "error": str(exc),
            "answer": "",
            "documents": [],
            "reference_keyword_coverage": 0.0,
            "citation_presence": 0.0,
            "citation_validity": 0.0,
            "citation_recall": 0.0,
            "latency_ms": (time.perf_counter() - start_time) * 1000,
        }

    total_latency_ms = (time.perf_counter() - start_time) * 1000

    answer = result.get("answer", "")
    documents = result.get("documents", [])

    citation_presence = calculate_citation_presence(answer)

    citation_validity = calculate_citation_validity(
        answer=answer,
        source_count=len(documents),
    )

    citation_recall = calculate_expected_citation_recall(
        answer=answer,
        retrieved_documents=documents,
        expected_chunk_indices=expected_citations,
    )

    correctness = calculate_keyword_correctness(
        answer,
        reference_answer
    )

    
    return {
        "status": "success",
        "question": question,
        "answer": answer,
        "documents": documents,
        "reference_keyword_coverage": correctness,
        "citation_presence": citation_presence,
        "citation_validity": citation_validity,
        "citation_recall": citation_recall,
        "latency_ms": total_latency_ms,
    }