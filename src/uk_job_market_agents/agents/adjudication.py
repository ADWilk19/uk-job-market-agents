from openai import OpenAI
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
    client = OpenAI()

    prompt = f"""
        You are adjudicating a disagreement between two job classifiers.

        Job title:
        {title}

        Job description:
        {description}

        Deterministic rules classification:
        {rules_value.value}

        LLM classification:
        {llm_value.value}

        Evaluate the advert itself rather than automatically trusting either classifier.

        Return:
        - the two supplied classifications
        - your recommended classification
        - concise evidence from the advert
        - concise reasoning

        The recommended classification must use the supplied RoleFamily schema.
    """

    response = client.responses.parse(
        model="gpt-5.6-luna",
        input=prompt,
        text_format=RoleFamilyAdjudication,
    )

    result = response.output_parsed

    if result is None:
        raise RuntimeError(
            "Role-family adjudicator did not return a parsed result"
        )

    return result


def _call_work_pattern_adjudicator(
    title: str,
    description: str,
    rules_value: WorkPattern,
    llm_value: WorkPattern,
) -> WorkPatternAdjudication:
    client = OpenAI()

    prompt = f"""
        You are adjudicating a disagreement between two job classifiers.

        Job title:
        {title}

        Job description:
        {description}

        Deterministic rules classification:
        {rules_value.value}

        LLM classification:
        {llm_value.value}

        Evaluate the actual working arrangement described by the advert.

        Distinguish between:
        - occasional meetings or exceptional attendance
        - recurring mandatory office attendance

        Return:
        - the two supplied classifications
        - your recommended classification
        - concise evidence from the advert
        - concise reasoning

        The recommended classification must use the supplied WorkPattern schema.
        """

    response = client.responses.parse(
        model="gpt-5.6-luna",
        input=prompt,
        text_format=WorkPatternAdjudication,
    )

    result = response.output_parsed

    if result is None:
        raise RuntimeError(
            "Work-pattern adjudicator did not return a parsed result"
        )

    return result
