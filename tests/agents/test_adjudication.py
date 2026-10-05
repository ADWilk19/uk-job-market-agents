import pytest
from pydantic import ValidationError

from uk_job_market_agents.agents.adjudication import (
    RoleFamilyAdjudication,
    WorkPatternAdjudication,
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
