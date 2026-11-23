"""Fill relevant_chunk_indices in evaluation/dataset.json from the portfolio chunks stored in Qdrant.

Chunk numbers change whenever data/portfolio.txt changes, so the dataset lists 'evidence' phrases instead:
short quotes that must appear in the chunks that answer each question. This script finds those chunks.

Run it after every portfolio ingest (inside the API container):
    docker compose exec api python -m scripts.rebuild_eval_dataset
"""
import hashlib
import json
import re
import sys
from pathlib import Path

DATASET = Path("evaluation/dataset.json")
PORTFOLIO = "data/portfolio.txt"


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def map_cases(cases: list[dict], chunks: list[tuple[int, str]]) -> list[str]:
    """Set relevant_chunk_indices / expected_citations on each case. Returns a list of problems."""
    normalized = [(index, _norm(text)) for index, text in chunks]
    problems = []

    for case in cases:
        found = set()
        for phrase in case["evidence"]:
            needle = _norm(phrase)
            hits = [index for index, text in normalized if needle in text]
            if not hits:
                problems.append(f"{case['id']}: evidence not found in any chunk: {phrase!r}")
            found.update(hits)

        case["relevant_chunk_indices"] = sorted(found)
        case["expected_citations"] = sorted(found)

    return problems


def main() -> int:
    from app.vectorstore.qdrant_store import QdrantVectorStore

    with open(PORTFOLIO, "rb") as file:
        file_hash = hashlib.sha256(file.read()).hexdigest()

    store = QdrantVectorStore(384)
    documents = store.get_documents(f"portfolio-{file_hash}")
    if not documents:
        print("The current data/portfolio.txt is not ingested. Run scripts/reingest_portfolio.py first.")
        return 1

    chunks = [(d.metadata.get("chunk_index", -1), d.page_content) for d in documents]

    dataset = json.loads(DATASET.read_text(encoding="utf-8"))
    problems = map_cases(dataset["cases"], chunks)

    DATASET.write_text(json.dumps(dataset, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"{len(chunks)} portfolio chunks, {len(dataset['cases'])} cases")
    for case in dataset["cases"]:
        print(f"  {case['id']}: {case['relevant_chunk_indices']}  {case['question']}")

    if problems:
        print("\nProblems (edit the evidence phrase so it sits inside one chunk, then run again):")
        for problem in problems:
            print("  " + problem)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
