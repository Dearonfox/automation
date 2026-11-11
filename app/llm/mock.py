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

