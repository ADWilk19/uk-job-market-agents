import pytest
from pydantic import ValidationError

from uk_job_market_agents.agents.workflow import ResolvedClassification
from uk_job_market_agents.models.job_posting import (
    RoleFamily,
    WorkPattern,
)


def test_resolved_classification_accepts_valid_values():
    result = ResolvedClassification(
        role_family=RoleFamily.DATA_SCIENCE,
        work_pattern=WorkPattern.HYBRID,
    )

    assert result.role_family == RoleFamily.DATA_SCIENCE
    assert result.work_pattern == WorkPattern.HYBRID


def test_resolved_classification_rejects_invalid_work_pattern():
    with pytest.raises(ValidationError):
        ResolvedClassification(
            role_family=RoleFamily.DATA_SCIENCE,
            work_pattern="mostly_remote",
        )
