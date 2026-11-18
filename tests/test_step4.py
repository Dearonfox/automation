from pathlib import Path

import pandas as pd
import pytest

from app.explain import SensorDeviation, explain_sample
from app.guide import GuideService
from app.llm import MockLLM
from app.rag.knowledge import load_knowledge_cases
from app.rag.store import KnowledgeStore


def complete(coroutine):
    try:
        coroutine.send(None)
    except StopIteration as completed:
        return completed.value
    raise AssertionError("Mock coroutine unexpectedly suspended")


def test_explain_sample_returns_largest_absolute_z_scores() -> None:
    reference = pd.DataFrame({"sensor_a": [0.0, 1.0, 2.0], "sensor_b": [10.0, 11.0, 12.0]})
    sample = pd.Series({"sensor_a": 10.0, "sensor_b": 11.0})
    deviations = explain_sample(reference, sample, top_n=2)
    assert deviations[0].sensor == "sensor_a"
    assert deviations[0].z_score > deviations[1].z_score


def test_requires_fifteen_synthetic_cases(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="15"):
        load_knowledge_cases(tmp_path)
    cases = load_knowledge_cases()
    assert len(cases) >= 15
    assert all(case.synthetic for case in cases)


def test_chroma_search_and_mock_guide_are_offline(tmp_path: Path) -> None:
    store = KnowledgeStore(tmp_path / "chroma")
    assert store.index() >= 15
    deviations = [SensorDeviation("sensor_050", 10.0, 1.0, 7.5)]
    retrieved = store.search(deviations, limit=3)
    assert len(retrieved) == 3
    assert all(case.case_id.startswith("SYN-") for case in retrieved)

    guide = complete(GuideService(MockLLM()).generate(deviations, retrieved))
    assert guide.requires_human_confirmation is True
    assert guide.source_case_ids == [case.case_id for case in retrieved]
    assert "설비 조작" in " ".join(guide.cautions)
