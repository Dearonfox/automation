from app.llm import MockLLM, create_llm


def test_mock_is_default_provider() -> None:
    assert isinstance(create_llm(), MockLLM)


def test_mock_llm_is_deterministic() -> None:
    coroutine = MockLLM().generate("evaluate change")
    try:
        coroutine.send(None)
    except StopIteration as completed:
        response = completed.value
    else:
        raise AssertionError("MockLLM should complete without external I/O")
    assert response.content == "[synthetic-analysis] evaluate change"
    assert response.provider == "mock"

