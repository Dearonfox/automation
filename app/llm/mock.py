import json

from app.llm.provider import LLMResponse


class MockLLM:
    """Deterministic provider used by default; never performs a network call."""

    async def generate(self, prompt: str, *, model: str | None = None) -> LLMResponse:
        selected_model = model or "mock-default"
        return LLMResponse(
            content=f"[synthetic-analysis] {prompt}",
            model=selected_model,
            provider="mock",
        )

    async def generate_structured(
        self, prompt: str, *, schema_name: str, model: str | None = None
    ) -> LLMResponse:
        if schema_name != "operator_guide":
            raise ValueError(f"Unsupported mock schema: {schema_name}")
        payload = json.loads(prompt)
        deviations = payload["deviations"]
        cases = payload["similar_cases"]
        sensors = ", ".join(item["sensor"] for item in deviations[:3])
        content = {
            "summary": f"익명 센서 {sensors}에서 큰 편차가 관찰되어 추가 확인이 필요합니다.",
            "check_items": [
                "알림 식별자와 발생 시각을 확인합니다.",
                "입력 데이터의 누락 여부와 표시된 편차값을 확인합니다.",
                "관찰 사실과 추가 확인이 필요한 사항을 구분해 기록합니다.",
                "관련 담당자에게 기록과 유사 사례 ID를 전달합니다.",
            ],
            "report_draft": (
                f"익명 센서 {sensors}에서 편차가 관찰되었습니다. 센서의 물리적 의미와 "
                "고장 원인은 확인되지 않았으며, 데이터 누락 및 관련 이력 확인이 필요합니다."
            ),
            "cautions": [
                "이 가이드는 가상 사례를 참고한 초안입니다.",
                "설비 조작, 생산 중단 또는 재개 판단은 승인된 현장 절차와 담당자 판단을 따릅니다.",
            ],
            "source_case_ids": [case["case_id"] for case in cases],
            "requires_human_confirmation": True,
        }
        return LLMResponse(
            content=json.dumps(content, ensure_ascii=False),
            model=model or "mock-structured",
            provider="mock",
        )

