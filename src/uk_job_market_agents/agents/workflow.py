from pydantic import BaseModel
from enum import Enum

from uk_job_market_agents.agents.adjudication import (
    RoleFamilyAdjudication,
    WorkPatternAdjudication,
    adjudicate_role_family,
    adjudicate_work_pattern,
)
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


class ReviewReason(str, Enum):
    ROLE_FAMILY = "role_family"
    WORK_PATTERN = "work_pattern"
    BOTH = "both"


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


class WorkflowResolution(BaseModel):
    resolved: ResolvedClassification | None
    requires_review: bool
    review_reason: ReviewReason | None


class AdjudicationResolution(BaseModel):
    proposed: ResolvedClassification
    requires_review: bool


class AdjudicatedWorkflowResult(BaseModel):
    workflow: ClassificationWorkflowResult
    role_family_adjudication: RoleFamilyAdjudication | None = None
    work_pattern_adjudication: WorkPatternAdjudication | None = None

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
            review_reason=None,
        )

    if not result.role_family_agrees and not result.work_pattern_agrees:
        reason = ReviewReason.BOTH
    elif not result.role_family_agrees:
        reason = ReviewReason.ROLE_FAMILY
    else:
        reason = ReviewReason.WORK_PATTERN

    return WorkflowResolution(
        resolved=None,
        requires_review=True,
        review_reason=reason,
    )


def adjudicate_workflow(
    title: str,
    description: str,
    result: ClassificationWorkflowResult,
) -> AdjudicatedWorkflowResult:
    role_adjudication = None
    work_adjudication = None

    if not result.role_family_agrees:
        role_adjudication = adjudicate_role_family(
            title=title,
            description=description,
            rules_value=result.rules_role_family,
            llm_value=result.llm.role_family,
        )

    if not result.work_pattern_agrees:
        work_adjudication = adjudicate_work_pattern(
            title=title,
            description=description,
            rules_value=result.rules_work_pattern,
            llm_value=result.llm.work_pattern,
        )

    return AdjudicatedWorkflowResult(
        workflow=result,
        role_family_adjudication=role_adjudication,
        work_pattern_adjudication=work_adjudication,
    )


def resolve_after_adjudication(
    result: AdjudicatedWorkflowResult,
) -> AdjudicationResolution:
    workflow = result.workflow

    role_family = (
        result.role_family_adjudication.recommended_value
        if result.role_family_adjudication is not None
        else workflow.rules_role_family
    )

    work_pattern = (
        result.work_pattern_adjudication.recommended_value
        if result.work_pattern_adjudication is not None
        else workflow.rules_work_pattern
    )

    return AdjudicationResolution(
        proposed=ResolvedClassification(
            role_family=role_family,
            work_pattern=work_pattern,
        ),
        requires_review=(
            result.role_family_adjudication is not None
            or result.work_pattern_adjudication is not None
        ),
    )
