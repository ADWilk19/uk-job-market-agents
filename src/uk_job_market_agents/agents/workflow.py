from pydantic import BaseModel

from uk_job_market_agents.agents.classifier import ClassificationResult
from uk_job_market_agents.models.job_posting import (
    RoleFamily,
    WorkPattern,
)


class ResolvedClassification(BaseModel):
    role_family: RoleFamily
    work_pattern: WorkPattern


class ClassificationWorkflowResult(BaseModel):
    rules_role_family: RoleFamily
    rules_work_pattern: WorkPattern

    llm: ClassificationResult

    role_family_agrees: bool
    work_pattern_agrees: bool
