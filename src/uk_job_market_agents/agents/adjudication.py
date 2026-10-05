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


def adjudicate_role_family(
    title: str,
    description: str,
    rules_value: RoleFamily,
    llm_value: RoleFamily,
) -> RoleFamilyAdjudication:
    return _call_role_family_adjudicator(
        title,
        description,
        rules_value,
        llm_value,
    )


def adjudicate_work_pattern(
    title: str,
    description: str,
    rules_value: WorkPattern,
    llm_value: WorkPattern,
) -> WorkPatternAdjudication:
    return _call_work_pattern_adjudicator(
        title,
        description,
        rules_value,
        llm_value,
    )


def _call_role_family_adjudicator(
    title: str,
    description: str,
    rules_value: RoleFamily,
    llm_value: RoleFamily,
) -> RoleFamilyAdjudication:
    raise NotImplementedError


def _call_work_pattern_adjudicator(
    title: str,
    description: str,
    rules_value: WorkPattern,
    llm_value: WorkPattern,
) -> WorkPatternAdjudication:
    raise NotImplementedError
