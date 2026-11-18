import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class KnowledgeCase:
    case_id: str
    title: str
    signal_pattern: str
    observations: list[str]
    check_items: list[str]
    handover_notes: list[str]
    synthetic: bool

    @property
    def document(self) -> str:
        return " ".join(
            [
                self.title,
                self.signal_pattern,
                *self.observations,
                *self.check_items,
                *self.handover_notes,
            ]
        )


def load_knowledge_cases(directory: Path = Path("data/knowledge")) -> list[KnowledgeCase]:
    cases: list[KnowledgeCase] = []
    for path in sorted(directory.glob("case_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        case = KnowledgeCase(**payload)
        if not case.synthetic:
            raise ValueError(f"Knowledge case must be marked synthetic: {path}")
        cases.append(case)
    if len(cases) < 15:
        raise ValueError(f"At least 15 synthetic knowledge cases are required; found {len(cases)}")
    return cases
