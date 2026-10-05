from pydantic import BaseModel

from uk_job_market_agents.models.job_posting import (
    RoleFamily,
    WorkPattern,
)


class RoleFamilyAdjudication(BaseModel):
    rules_value: RoleFamily
    llm_value: RoleFamily
    recommended_value: RoleFamily
    evidence: list[str]
    reasoning: str


class WorkPatternAdjudication(BaseModel):
    rules_value: WorkPattern
    llm_value: WorkPattern
    recommended_value: WorkPattern
    evidence: list[str]
    reasoning: str
