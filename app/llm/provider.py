from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class LLMResponse:
    content: str
    model: str
    provider: str


class LLMProvider(Protocol):
    async def generate(self, prompt: str, *, model: str | None = None) -> LLMResponse: ...

