from functools import lru_cache
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator

from app.analysis import AnalysisEngine
from app.core.config import get_settings
from app.core.database import AnalysisRecord, AnalysisRepository
from app.notify import NullNotifier, SlackWebhookNotifier
from app.rag import KnowledgeStore

router = APIRouter(prefix="/api/v1", tags=["analyses"])


class AnalysisRequest(BaseModel):
    sample_index: int | None = None
    features: dict[str, float] | None = None

    @model_validator(mode="after")
    def exactly_one_input(self) -> "AnalysisRequest":
        if (self.sample_index is None) == (self.features is None):
            raise ValueError("Provide exactly one of sample_index or features")
        return self


class ActionRequest(BaseModel):
    action: Literal["acknowledged", "report_prepared", "confirmed", "rejected"]
    actor: str = Field(min_length=1, max_length=100)
    note: str = Field(default="", max_length=2000)


class AnalysisResponse(BaseModel):
    analysis_id: str
    created_at: str
    sample_index: int | None
    anomalous: bool
    status: str
    result: dict[str, object]
    actions: list[dict[str, str]] = Field(default_factory=list)
    does_not_authorize_production: bool = True


@lru_cache
def get_repository() -> AnalysisRepository:
    return AnalysisRepository(get_settings().database_path)


@lru_cache
def get_engine() -> AnalysisEngine:
    settings = get_settings()
    notifier = (
        SlackWebhookNotifier(settings.slack_webhook_url)
        if settings.slack_webhook_url
        else NullNotifier()
    )
    return AnalysisEngine(
        get_repository(), KnowledgeStore(settings.chroma_path), notifier=notifier
    )


EngineDependency = Annotated[AnalysisEngine, Depends(get_engine)]
RepositoryDependency = Annotated[AnalysisRepository, Depends(get_repository)]


def to_response(record: AnalysisRecord, repository: AnalysisRepository) -> AnalysisResponse:
    return AnalysisResponse(
        **record.__dict__, actions=repository.list_actions(record.analysis_id)
    )


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(
    request: AnalysisRequest,
    engine: EngineDependency,
) -> AnalysisResponse:
    try:
        record = await engine.analyze(
            sample_index=request.sample_index, features=request.features
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return to_response(record, engine.repository)


@router.get("/analyses/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(
    analysis_id: str, repository: RepositoryDependency
) -> AnalysisResponse:
    record = repository.get(analysis_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return to_response(record, repository)


@router.post("/analyses/{analysis_id}/actions", response_model=AnalysisResponse)
def add_action(
    analysis_id: str,
    request: ActionRequest,
    repository: RepositoryDependency,
) -> AnalysisResponse:
    try:
        record = repository.add_action(
            analysis_id, actor=request.actor, action=request.action, note=request.note
        )
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Analysis not found") from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return to_response(record, repository)
