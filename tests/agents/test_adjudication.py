import pytest
from pydantic import ValidationError

from uk_job_market_agents.agents.adjudication import (
    RoleFamilyAdjudication,
    WorkPatternAdjudication,
    adjudicate_role_family,
    adjudicate_work_pattern,
)
from uk_job_market_agents.models.job_posting import (
    RoleFamily,
    WorkPattern,
)


def test_role_family_adjudication_accepts_valid_values():
    result = RoleFamilyAdjudication(
        rules_value=RoleFamily.DATA_ENGINEERING,
        llm_value=RoleFamily.ANALYTICS_ENGINEERING,
        recommended_value=RoleFamily.DATA_ENGINEERING,
        evidence=[
            "The advert focuses on production data-platform work.",
            "It also mentions dbt and semantic models.",
        ],
        reasoning="The engineering responsibilities are broader than analytics engineering.",
    )

    assert result.recommended_value == RoleFamily.DATA_ENGINEERING


def test_work_pattern_adjudication_accepts_valid_values():
    result = WorkPatternAdjudication(
        rules_value=WorkPattern.REMOTE,
        llm_value=WorkPattern.HYBRID,
        recommended_value=WorkPattern.HYBRID,
        evidence=[
            "The advert says remote-first.",
            "Attendance is required every Tuesday and Thursday.",
        ],
        reasoning="Recurring mandatory office attendance makes the role hybrid.",
    )

    assert result.recommended_value == WorkPattern.HYBRID


def test_adjudication_rejects_invalid_recommendation():
    with pytest.raises(ValidationError):
        WorkPatternAdjudication(
            rules_value=WorkPattern.REMOTE,
            llm_value=WorkPattern.HYBRID,
            recommended_value="mostly_remote",
            evidence=["The advert contains mixed signals."],
            reasoning="The role is mostly remote.",
        )


def test_adjudicate_role_family_returns_structured_result(monkeypatch):
    expected = RoleFamilyAdjudication(
        rules_value=RoleFamily.DATA_ENGINEERING,
        llm_value=RoleFamily.ANALYTICS_ENGINEERING,
        recommended_value=RoleFamily.DATA_ENGINEERING,
        evidence=[
            "The role owns production data-platform work.",
            "dbt and semantic modelling are supporting responsibilities.",
        ],
        reasoning="The broader responsibilities align more closely with data engineering.",
    )

    def fake_call(
        title: str,
        description: str,
        rules_value: RoleFamily,
        llm_value: RoleFamily,
    ) -> RoleFamilyAdjudication:
        return expected

    monkeypatch.setattr(
        "uk_job_market_agents.agents.adjudication._call_role_family_adjudicator",
        fake_call,
    )

    result = adjudicate_role_family(
        "Data Platform Specialist",
        "Build ELT pipelines, maintain dbt models and optimise Snowflake.",
        RoleFamily.DATA_ENGINEERING,
        RoleFamily.ANALYTICS_ENGINEERING,
    )

    assert result == expected


def test_adjudicate_work_pattern_returns_structured_result(monkeypatch):
    expected = WorkPatternAdjudication(
        rules_value=WorkPattern.REMOTE,
        llm_value=WorkPattern.HYBRID,
        recommended_value=WorkPattern.HYBRID,
        evidence=[
            "The advert says remote-first.",
            "Office attendance is mandatory every Tuesday and Thursday.",
        ],
        reasoning="Recurring mandatory attendance makes the role hybrid.",
    )

    def fake_call(
        title: str,
        description: str,
        rules_value: WorkPattern,
        llm_value: WorkPattern,
    ) -> WorkPatternAdjudication:
        return expected

    monkeypatch.setattr(
        "uk_job_market_agents.agents.adjudication._call_work_pattern_adjudicator",
        fake_call,
    )

    result = adjudicate_work_pattern(
        "Data Scientist",
        (
            "This is a remote-first role. "
            "Attendance at the Manchester office is required every Tuesday and Thursday."
        ),
        WorkPattern.REMOTE,
        WorkPattern.HYBRID,
    )

    assert result == expected
