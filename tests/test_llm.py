import pytest

from app.llm import MockLLM, create_llm


def test_mock_is_default_provider() -> None:
    assert isinstance(create_llm(), MockLLM)


@pytest.mark.asyncio
async def test_mock_llm_is_deterministic() -> None:
    response = await MockLLM().generate("evaluate change")
    assert response.content == "[synthetic-analysis] evaluate change"
    assert response.provider == "mock"

