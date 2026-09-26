import json
from pathlib import Path

DATASET_PATH = Path("evaluation/dataset.json")

def load_evaluation_dataset():
    with DATASET_PATH.open("r", encoding="utf-8") as file:
        dataset = json.load(file)

    return dataset["cases"]