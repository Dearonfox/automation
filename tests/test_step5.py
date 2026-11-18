from pathlib import Path

import pytest
from pydantic import ValidationError

from app.api.analyses import AnalysisRequest
from app.core.database import AnalysisRepository


def test_analysis_request_requires_exactly_one_input() -> None:
    assert AnalysisRequest(sample_index=1254).sample_index == 1254
    assert AnalysisRequest(features={"sensor_001": 1.0}).features is not None
    with pytest.raises(ValidationError):
        AnalysisRequest()
    with pytest.raises(ValidationError):
        AnalysisRequest(sample_index=1, features={"sensor_001": 1.0})


def test_repository_records_review_workflow(tmp_path: Path) -> None:
    repository = AnalysisRepository(tmp_path / "automation.db")
    record = repository.create(
        {"prediction": "anomaly"}, sample_index=1254, anomalous=True
    )
    assert record.status == "review_required"

    acknowledged = repository.add_action(
        record.analysis_id, actor="operator-demo", action="acknowledged", note="확인 시작"
    )
    assert acknowledged.status == "acknowledged"
    prepared = repository.add_action(
        record.analysis_id,
        actor="operator-demo",
        action="report_prepared",
        note="보고 초안 작성",
    )
    assert prepared.status == "report_prepared"
    confirmed = repository.add_action(
        record.analysis_id,
        actor="operator-demo",
        action="confirmed",
        note="기록 확인 완료",
    )
    assert confirmed.status == "confirmed"
    assert len(repository.list_actions(record.analysis_id)) == 3
    with pytest.raises(ValueError, match="Invalid transition"):
        repository.add_action(
            record.analysis_id, actor="operator-demo", action="rejected", note="late"
        )
