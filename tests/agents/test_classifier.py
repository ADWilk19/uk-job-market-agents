import pytest
from pydantic import ValidationError

from uk_job_market_agents.agents.classifier import ClassificationResult
from uk_job_market_agents.models.job_posting import RoleFamily, WorkPattern


def test_classification_result_accepts_valid_values():
    result = ClassificationResult(
        role_family=RoleFamily.DATA_SCIENCE,
        work_pattern=WorkPattern.HYBRID,
        reasoning=(
            "The role builds forecasting models and requires "
            "office attendance every Tuesday and Thursday."
        ),
    )

    assert result.role_family == RoleFamily.DATA_SCIENCE
    assert result.work_pattern == WorkPattern.HYBRID


def test_classification_result_rejects_invalid_work_pattern():
    with pytest.raises(ValidationError):
        ClassificationResult(
            role_family=RoleFamily.DATA_SCIENCE,
            work_pattern="mostly_remote",
            reasoning="The advert describes the role as remote-first.",
        )
