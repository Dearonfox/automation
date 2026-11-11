from app.core.config import Settings, get_settings
from app.llm.mock import MockLLM
from app.llm.provider import LLMProvider


def create_llm(settings: Settings | None = None) -> LLMProvider:
    configured = settings or get_settings()
    if configured.llm_provider == "mock":
        return MockLLM()
    raise ValueError(f"Unsupported LLM provider: {configured.llm_provider}")

