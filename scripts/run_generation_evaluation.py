import asyncio
from app.vectorstore.qdrant_store import QdrantVectorStore
from app.llm.factory import create_llm
from app.graph.graph import create_rag_graph
from app.rag.prompt import RAG_PROMPT
from app.evaluation.dataset import load_evaluation_dataset
from app.evaluation.evaluation_runner import evaluate_generation_case
from app.retrieval.pipeline import create_retrieval_pipeline
from app.services.bm25_index_service import BM25IndexService

DATASET = load_evaluation_dataset()


def main():

    vector_store = QdrantVectorStore(
        embedding_dimension=384
    )

    llm = create_llm()

    bm25_index_service = BM25IndexService()

    retriever = create_retrieval_pipeline(
        vector_store=vector_store,
        llm=llm.llm,
        k=10,
        top_n=3,
        search_type="mmr",
        bm25_index_service=bm25_index_service,
    )

    graph = create_rag_graph(
        retriever=retriever,
        prompt=RAG_PROMPT,
        llm=llm.llm,
    )

    total_keyword_coverage = 0.0
    total_citation_presence = 0.0
    total_citation_validity = 0.0
    total_citation_recall = 0.0
    total_latency = 0.0

    results = []

    for item in DATASET:

        print("\n" + "=" * 70)
        print(f"QUESTION: {item['question']}")
        print("=" * 70)

        result = evaluate_generation_case(
            question=item["question"],
            reference_answer=item["reference_answer"],
            expected_citations=item.get(
                "expected_citations",
                item["relevant_chunk_indices"],
            ),
            rag_graph=graph,
            evaluator_llm=llm.llm,
            user_id="evaluation_user",
            session_id="evaluation_session",
        )

        results.append(result)

        if result["status"] != "success":
            print(f"\nEvaluation skipped: {result['status']}")
            continue

        total_keyword_coverage += result["reference_keyword_coverage"]
        total_citation_presence += result["citation_presence"]
        total_citation_validity += result["citation_validity"]
        total_citation_recall += result["citation_recall"]
        total_latency += result["latency_ms"]

        print("\nANSWER:")
        print(result["answer"])

        print("\nRETRIEVED CHUNKS:")
        print([
            document.get("metadata", {}).get("chunk_index")
            for document in result["documents"]
        ])

        print(
            f"\nReference_keyword_coverage: "
            f"{result['reference_keyword_coverage']:.2f}"
        )

        print(
            f"Citation Presence: "
            f"{result['citation_presence']:.2f}"
        )

        print(
            f"Citation Validity: "
            f"{result['citation_validity']:.2f}"
        )

        print(
            f"Citation Recall: "
            f"{result['citation_recall']:.2f}"
        )

        print(
            f"Latency: "
            f"{result['latency_ms']:.2f} ms"
        )

    successful_results = [
        result
        for result in results
        if result["status"] == "success"
    ]

    count = len(successful_results)

    print("\n" + "=" * 70)
    print("AVERAGE GENERATION EVALUATION")
    print("=" * 70)

    print(
        f"Average Reference_keyword_coverage: "
        f"{total_keyword_coverage / count:.2f}"
    )

    print(
        f"Average Citation Presence: "
        f"{total_citation_presence / count:.2f}"
    )

    print(
        f"Average Citation Validity: "
        f"{total_citation_validity / count:.2f}"
    )

    print(
        f"Average Citation Recall: "
        f"{total_citation_recall / count:.2f}"
    )

    print(
        f"Average Latency: "
        f"{total_latency / count:.2f} ms"
    )


if __name__ == "__main__":
    main()