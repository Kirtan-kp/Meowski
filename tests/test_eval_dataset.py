import json
from pathlib import Path

import pytest
from langchain_text_splitters import RecursiveCharacterTextSplitter

from scripts.rebuild_eval_dataset import map_cases


def _chunks():
    text = Path("data/portfolio.txt").read_text(encoding="utf-8")
    pieces = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50).split_text(text)
    return list(enumerate(pieces))


def test_every_evidence_phrase_sits_inside_a_portfolio_chunk():
    dataset = json.loads(Path("evaluation/dataset.json").read_text(encoding="utf-8"))
    problems = map_cases(dataset["cases"], _chunks())
    assert problems == []
    assert all(case["relevant_chunk_indices"] for case in dataset["cases"])


def test_map_cases_reports_missing_evidence():
    cases = [{"id": "x", "evidence": ["not in any chunk"]}]
    problems = map_cases(cases, [(0, "some other text")])
    assert len(problems) == 1 and cases[0]["relevant_chunk_indices"] == []


def test_loader_refuses_unmapped_dataset(tmp_path, monkeypatch):
    from app.evaluation import dataset as module

    path = tmp_path / "dataset.json"
    path.write_text(json.dumps({"cases": [{"id": "a", "relevant_chunk_indices": []}]}))
    monkeypatch.setattr(module, "DATASET_PATH", path)
    with pytest.raises(ValueError):
        module.load_evaluation_dataset()
