import json

from app.explain import SensorDeviation
from app.guide.schema import OperatorGuide
from app.llm import LLMProvider
from app.rag import RetrievedCase


class GuideService:
    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    async def generate(
        self, deviations: list[SensorDeviation], cases: list[RetrievedCase]
    ) -> OperatorGuide:
        payload = {
            "constraints": [
                "센서 의미를 추정하지 않는다",
                "설비 조작이나 생산 재개를 지시하지 않는다",
                "관찰 사실과 추가 확인 항목을 구분한다",
            ],
            "deviations": [item.__dict__ for item in deviations],
            "similar_cases": [
                {"case_id": case.case_id, "title": case.title, "document": case.document}
                for case in cases
            ],
        }
        response = await self.provider.generate_structured(
            json.dumps(payload, ensure_ascii=False), schema_name="operator_guide"
        )
        guide = OperatorGuide.model_validate_json(response.content)
        expected_ids = [case.case_id for case in cases]
        if guide.source_case_ids != expected_ids:
            raise ValueError("Guide source_case_ids must match the retrieved cases")
        if not guide.requires_human_confirmation:
            raise ValueError("Operator guide must require human confirmation")
        return guide
