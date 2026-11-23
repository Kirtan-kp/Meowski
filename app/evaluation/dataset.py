import json
from pathlib import Path

DATASET_PATH = Path("evaluation/dataset.json")

def load_evaluation_dataset():
    with DATASET_PATH.open("r", encoding="utf-8") as file:
        dataset = json.load(file)

    cases = dataset["cases"]
    empty = [case["id"] for case in cases if not case.get("relevant_chunk_indices")]
    if empty:
        raise ValueError(
            f"{len(empty)} evaluation case(s) have no relevant_chunk_indices yet. "
            "Run: python -m scripts.rebuild_eval_dataset (after ingesting the portfolio)."
        )

    return cases
