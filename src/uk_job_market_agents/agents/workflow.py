from pydantic import BaseModel

from uk_job_market_agents.agents.classifier import (
    ClassificationResult,
    classify_with_llm,
    )
from uk_job_market_agents.classification.rules import (
    classify_role_family,
    classify_work_pattern,
)
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


def run_classification_workflow(
    title: str,
    description: str,
) -> ClassificationWorkflowResult:
    rules_role_family = classify_role_family(title, description)

    rules_work_pattern = classify_work_pattern(
        f"{title} {description}"
    )

    llm_result = classify_with_llm(
        title,
        description,
    )

    return ClassificationWorkflowResult.from_results(
        rules_role_family=rules_role_family,
        rules_work_pattern=rules_work_pattern,
        llm=llm_result,
    )


class WorkflowResolution(BaseModel):
    resolved: ResolvedClassification | None
    requires_review: bool


def resolve_classification(
    result: ClassificationWorkflowResult,
) -> WorkflowResolution:
    if result.role_family_agrees and result.work_pattern_agrees:
        return WorkflowResolution(
            resolved=ResolvedClassification(
                role_family=result.rules_role_family,
                work_pattern=result.rules_work_pattern,
            ),
            requires_review=False,
        )

    return WorkflowResolution(
        resolved=None,
        requires_review=True,
    )
