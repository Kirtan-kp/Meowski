from langchain_core.documents import Document

from scripts.run_retrieval_evaluation import (
    calculate_recall,
    calculate_precision,
    calculate_mrr,
)


def make_documents(indices):
    return [
        Document(
            page_content=f"Document {index}",
            metadata={"chunk_index": index},
        )
        for index in indices
    ]


def test_calculate_recall():
    retrieved = make_documents([0, 1, 2])
    relevant = [0, 2]

    assert calculate_recall(retrieved, relevant) == 1.0


def test_calculate_recall_partial():
    retrieved = make_documents([0, 1])
    relevant = [0, 2]

    assert calculate_recall(retrieved, relevant) == 0.5


def test_calculate_recall_with_no_relevant_chunks():
    retrieved = make_documents([0, 1])

    assert calculate_recall(retrieved, []) == 0.0


def test_calculate_precision():
    retrieved = make_documents([0, 1, 2])
    relevant = [0, 2]

    assert calculate_precision(retrieved, relevant) == 2 / 3


def test_calculate_precision_with_no_retrieved_documents():
    retrieved = []

    assert calculate_precision(retrieved, [0, 1]) == 0.0


def test_calculate_mrr():
    retrieved = make_documents([1, 0, 2])
    relevant = [0, 2]

    assert calculate_mrr(retrieved, relevant) == 0.5


def test_calculate_mrr_when_no_relevant_document_is_retrieved():
    retrieved = make_documents([1, 3, 4])
    relevant = [0, 2]

    assert calculate_mrr(retrieved, relevant) == 0.0