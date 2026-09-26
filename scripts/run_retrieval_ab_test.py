from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.vectorstore.qdrant_store import QdrantVectorStore
from app.retrieval.vector_retriever import create_vector_retriever
from app.retrieval.bm25_retriever import create_bm25_retriever
from app.retrieval.pipeline import RuntimeFilteredEnsembleRetriever
from app.retrieval.reranker import create_reranker
from app.evaluation.dataset import load_evaluation_dataset


K = 3

EVALUATION_DATASET = load_evaluation_dataset()


vector_store = QdrantVectorStore(
    embedding_dimension=384
)


user_filter = Filter(
    must=[
        FieldCondition(
            key="metadata.scope",
            match=MatchValue(value="portfolio")
        )
    ]
)


vector_retriever = create_vector_retriever(
    vector_store=vector_store,
    k=20,
    search_type="mmr",
    search_kwargs=None
)


bm25_retriever = create_bm25_retriever(
    vector_store=vector_store,
    filter=user_filter,
    k=20
)


hybrid_retriever = RuntimeFilteredEnsembleRetriever(
    vector_retriever=vector_retriever,
    bm25_retriever=bm25_retriever,
    weights=[0.5, 0.5],
    candidate_limit=30,
    default_filter=user_filter
)


reranker = create_reranker(
    retriever=hybrid_retriever,
    top_n=K
)


def get_chunk_index(document):
    return document.metadata.get("chunk_index")


def calculate_recall(retrieved, relevant):
    retrieved_indices = {
        get_chunk_index(document)
        for document in retrieved
    }

    relevant = set(relevant)

    if not relevant:
        return 0.0

    return len(retrieved_indices & relevant) / len(relevant)


def calculate_precision(retrieved, relevant):
    retrieved_indices = {
        get_chunk_index(document)
        for document in retrieved
    }

    relevant = set(relevant)

    if not retrieved_indices:
        return 0.0

    return len(retrieved_indices & relevant) / len(retrieved_indices)


def calculate_mrr(retrieved, relevant):
    relevant = set(relevant)

    for rank, document in enumerate(retrieved, start=1):
        chunk_index = get_chunk_index(document)

        if chunk_index in relevant:
            return 1.0 / rank

    return 0.0


def calculate_hit_rate(retrieved, relevant):
    retrieved_indices = {
        get_chunk_index(document)
        for document in retrieved
    }

    relevant = set(relevant)

    return float(bool(retrieved_indices & relevant))


def evaluate_retriever(name, retriever):

    total_recall = 0.0
    total_precision = 0.0
    total_mrr = 0.0
    total_hit_rate = 0.0

    print("\n" + "=" * 70)
    print(name)
    print("=" * 70)

    for item in EVALUATION_DATASET:

        question = item["question"]
        relevant = item["relevant_chunk_indices"]

        documents = retriever.invoke(question)
        documents = documents[:K]

        retrieved_indices = [
            get_chunk_index(document)
            for document in documents
        ]

        recall = calculate_recall(
            documents,
            relevant
        )

        precision = calculate_precision(
            documents,
            relevant
        )

        mrr = calculate_mrr(
            documents,
            relevant
        )

        hit_rate = calculate_hit_rate(
            documents,
            relevant
        )

        total_recall += recall
        total_precision += precision
        total_mrr += mrr
        total_hit_rate += hit_rate

        print(f"\nQUESTION: {question}")
        print(f"Expected:  {relevant}")
        print(f"Retrieved: {retrieved_indices}")
        print(f"Recall@{K}: {recall:.2f}")
        print(f"Precision@{K}: {precision:.2f}")
        print(f"MRR@{K}: {mrr:.2f}")
        print(f"Hit Rate@{K}: {hit_rate:.2f}")

    count = len(EVALUATION_DATASET)

    results = {
        "recall": total_recall / count,
        "precision": total_precision / count,
        "mrr": total_mrr / count,
        "hit_rate": total_hit_rate / count
    }

    print("\nAVERAGE")
    print(f"Recall@{K}: {results['recall']:.2f}")
    print(f"Precision@{K}: {results['precision']:.2f}")
    print(f"MRR@{K}: {results['mrr']:.2f}")
    print(f"Hit Rate@{K}: {results['hit_rate']:.2f}")

    return results


if __name__ == "__main__":

    # A — Hybrid RRF only
    rrf_results = evaluate_retriever(
        "A — HYBRID RRF ONLY",
        hybrid_retriever
    )

    # B — Hybrid RRF + Cross-Encoder
    reranked_results = evaluate_retriever(
        "B — HYBRID RRF + CROSS-ENCODER",
        reranker
    )

    print("\n" + "=" * 70)
    print("A/B COMPARISON")
    print("=" * 70)

    print(
        f"\n{'Metric':<15}"
        f"{'RRF':>12}"
        f"{'Reranked':>15}"
        f"{'Delta':>12}"
    )

    print("-" * 54)

    for metric in [
        "recall",
        "precision",
        "mrr",
        "hit_rate"
    ]:
        rrf = rrf_results[metric]
        reranked = reranked_results[metric]
        delta = reranked - rrf

        print(
            f"{metric:<15}"
            f"{rrf:>12.2f}"
            f"{reranked:>15.2f}"
            f"{delta:>12.2f}"
        )