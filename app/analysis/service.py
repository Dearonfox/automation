from dataclasses import asdict

import pandas as pd

from app.core.database import AnalysisRecord, AnalysisRepository
from app.data import load_secom, prepare_chronological_split
from app.detect import fit_random_forest
from app.explain import explain_sample
from app.guide import GuideService
from app.llm import create_llm
from app.notify.slack import Notifier, NullNotifier
from app.rag import KnowledgeStore


class AnalysisEngine:
    def __init__(
        self,
        repository: AnalysisRepository,
        knowledge_store: KnowledgeStore,
        notifier: Notifier | None = None,
    ) -> None:
        self.repository = repository
        self.knowledge_store = knowledge_store
        self.notifier = notifier or NullNotifier()
        self.prepared = prepare_chronological_split(load_secom())
        self.detector = fit_random_forest(self.prepared.x_train, self.prepared.y_train)
        self.normal_reference = self.prepared.x_train.loc[
            self.prepared.y_train.to_numpy() == -1
        ]
        self.knowledge_store.index()
        self.guide_service = GuideService(create_llm())

    def resolve_sample(
        self, *, sample_index: int | None, features: dict[str, float] | None
    ) -> tuple[pd.DataFrame, int | None]:
        if (sample_index is None) == (features is None):
            raise ValueError("Provide exactly one of sample_index or features")
        if sample_index is not None:
            if sample_index not in self.prepared.x_test.index:
                raise ValueError("sample_index must identify a row in the chronological test split")
            return self.prepared.x_test.loc[[sample_index]], sample_index
        assert features is not None
        expected = list(self.prepared.x_train.columns)
        if set(features) != set(expected):
            missing = sorted(set(expected) - set(features))
            extra = sorted(set(features) - set(expected))
            raise ValueError(
                f"features must contain the 468 preprocessed sensors; "
                f"missing={missing[:5]}, extra={extra[:5]}"
            )
        frame = pd.DataFrame([[features[name] for name in expected]], columns=expected)
        return frame, None

    async def analyze(
        self, *, sample_index: int | None = None, features: dict[str, float] | None = None
    ) -> AnalysisRecord:
        frame, resolved_index = self.resolve_sample(sample_index=sample_index, features=features)
        prediction = self.detector.predict(frame).predictions.iloc[0]
        deviations = explain_sample(self.normal_reference, frame.iloc[0], top_n=5)
        cases = self.knowledge_store.search(deviations, limit=3)
        guide = await self.guide_service.generate(deviations, cases)
        anomalous = bool(prediction == 1)
        result: dict[str, object] = {
            "model": "RandomForest",
            "prediction": "anomaly" if anomalous else "normal",
            "top_deviations": [asdict(item) for item in deviations],
            "retrieved_cases": [
                {"case_id": case.case_id, "title": case.title, "distance": case.distance}
                for case in cases
            ],
            "guide": guide.model_dump(),
            "limitations": [
                "센서 의미가 익명화되어 물리적 원인과 실제 조치를 판단할 수 없습니다.",
                "모델의 정상 판정은 공정 안전이나 생산 재개를 보장하지 않습니다.",
            ],
        }
        record = self.repository.create(
            result, sample_index=resolved_index, anomalous=anomalous
        )
        if anomalous:
            await self.notifier.notify(
                f"[automation] 이상 분석 {record.analysis_id}: 작업자 검토가 필요합니다."
            )
        return record
