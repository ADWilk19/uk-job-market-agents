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


    @classmethod
    def from_results(
        cls,
        *,
        rules_role_family: RoleFamily,
        rules_work_pattern: WorkPattern,
        llm: ClassificationResult,
    ) -> "ClassificationWorkflowResult":
        return cls(
            rules_role_family=rules_role_family,
            rules_work_pattern=rules_work_pattern,
            llm=llm,
            role_family_agrees=rules_role_family == llm.role_family,
            work_pattern_agrees=rules_work_pattern == llm.work_pattern,
        )
