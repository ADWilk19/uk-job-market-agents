import pytest
from pydantic import ValidationError

from uk_job_market_agents.agents.classifier import ClassificationResult
from uk_job_market_agents.agents.workflow import (
    ClassificationWorkflowResult,
    ResolvedClassification,
)
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


def test_workflow_result_preserves_classifier_outputs():
    llm_result = ClassificationResult(
        role_family=RoleFamily.DATA_SCIENCE,
        work_pattern=WorkPattern.HYBRID,
        reasoning="Mandatory office attendance twice per week.",
    )

    result = ClassificationWorkflowResult(
        rules_role_family=RoleFamily.DATA_SCIENCE,
        rules_work_pattern=WorkPattern.REMOTE,
        llm=llm_result,
        role_family_agrees=True,
        work_pattern_agrees=False,
    )

    assert result.rules_role_family == RoleFamily.DATA_SCIENCE
    assert result.rules_work_pattern == WorkPattern.REMOTE

    assert result.llm.role_family == RoleFamily.DATA_SCIENCE
    assert result.llm.work_pattern == WorkPattern.HYBRID

    assert result.role_family_agrees is True
    assert result.work_pattern_agrees is False


def test_workflow_result_can_record_full_agreement():
    llm_result = ClassificationResult(
        role_family=RoleFamily.DATA_ENGINEERING,
        work_pattern=WorkPattern.REMOTE,
        reasoning="The advert explicitly describes a remote data engineering role.",
    )

    result = ClassificationWorkflowResult(
        rules_role_family=RoleFamily.DATA_ENGINEERING,
        rules_work_pattern=WorkPattern.REMOTE,
        llm=llm_result,
        role_family_agrees=True,
        work_pattern_agrees=True,
    )

    assert result.role_family_agrees is True
    assert result.work_pattern_agrees is True
