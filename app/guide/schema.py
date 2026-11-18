from pydantic import BaseModel, Field


class OperatorGuide(BaseModel):
    summary: str
    check_items: list[str] = Field(min_length=1)
    report_draft: str
    cautions: list[str] = Field(min_length=1)
    source_case_ids: list[str]
    requires_human_confirmation: bool
