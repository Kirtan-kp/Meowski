from qdrant_client.models import Filter, FieldCondition, MatchValue
from app.vectorstore.qdrant_store import QdrantVectorStore
from app.retrieval.pipeline import create_retrieval_pipeline
from app.llm.providers.groq import GroqLLM
from app.evaluation.dataset import load_evaluation_dataset
from app.services.bm25_index_service import BM25IndexService

from app.evaluation.retrieval_metrics import (
    calculate_recall,
    calculate_precision,
    calculate_mrr,
    calculate_hit_rate
)

EVALUATION_DATASET = load_evaluation_dataset()

vector_store = QdrantVectorStore(embedding_dimension = 384)

# user_filter = Filter(
#     must=[
#         FieldCondition(
#             key = "metadata.user_id",
#             match=MatchValue(value = "user_1")
#         ),
#         FieldCondition(
#             key = "metadata.session_id",
#             match=MatchValue(value = "session_1")
#         )
#     ]
# )

user_filter = Filter(
    must=[
        FieldCondition(
            key="metadata.scope",
            match=MatchValue(value="portfolio")
        )
    ]
)

llm = GroqLLM()

# Same configuration as the live API (hybrid dense + BM25 with RRF, then reranking).
retriever = create_retrieval_pipeline(vector_store = vector_store , llm = llm.llm , k = 10 , top_n = 3 , search_type = "mmr" , filter = user_filter , bm25_index_service = BM25IndexService())

def get_chunk_index(document):
    return document.metadata.get("chunk_index")

def calculate_recall(retrieved , relevant):

    retrieved_indices = {get_chunk_index(document) for document in retrieved}
    relevant = set(relevant)

    if not relevant:
        return 0.0

    return len(retrieved_indices & relevant) / len(relevant)

def calculate_precision(retrieved , relevant):

    retrieved_indices = {get_chunk_index(document) for document in retrieved}
    relevant = set(relevant)

    if not retrieved_indices:
        return 0.0

    return len(retrieved_indices & relevant) / len(retrieved_indices)


def calculate_mrr(retrieved , relevant):

    relevant = set(relevant)

    for rank , document in enumerate(retrieved , start = 1):
        chunk_index = get_chunk_index(document)

        if chunk_index in relevant:
            return 1.0 / rank

    return 0.0

def evaluate_retrieval(k):

    total_recall = 0.0
    total_precision = 0.0
    total_mrr = 0.0
    total_hit_rate = 0.0

    print(
        f"\n================ RETRIEVAL EVALUATION @ {k} ================\n"
    )

    for item in EVALUATION_DATASET:

        question = item["question"]
        relevant = item["relevant_chunk_indices"]
        documents = retriever.invoke(question)
        documents = documents[:k]

        recall = calculate_recall(documents , relevant)
        precision = calculate_precision(documents , relevant)
        mrr = calculate_mrr(documents , relevant)
        hit_rate = calculate_hit_rate(documents, relevant)

        total_recall += recall
        total_precision += precision
        total_mrr += mrr
        total_hit_rate += hit_rate

        print(f"QUESTION: {question}")

        print(f"Expected chunks: {relevant}")

        print("Retrieved chunks:" , [get_chunk_index(document) for document in documents])
        for document in documents:
            snippet = " ".join(document.page_content.split())[:90]
            print(f"    [{get_chunk_index(document)}] {snippet}")

        print(f"Recall@{k} : {recall:.2f}")
        print(f"Precision@{k} : {precision:.2f}")
        print(f"MRR@{k} : {mrr:.2f}")
        print(f"Hit Rate@{k} : {hit_rate:.2f}")

        print("-" * 55)

    count = len(EVALUATION_DATASET)

    average_recall = total_recall / count
    average_precision = total_precision / count
    average_mrr = total_mrr / count
    average_hit_rate = total_hit_rate / count

    print("\n================ AVERAGE =================\n")

    print(f"Average Recall@{k}: {average_recall:.2f}")
    print(f"Average Precision@{k}: {average_precision:.2f}")
    print(f"Average MRR@{k}: {average_mrr:.2f}")
    print(f"Average Hit Rate@{k}: {average_hit_rate:.2f}")

    print("\n=======================================================\n")

    return {"recall" : average_recall , "precision" : average_precision , "mrr" : average_mrr , "hit_rate": average_hit_rate}


if __name__ == "__main__":

    evaluate_retrieval(3)   