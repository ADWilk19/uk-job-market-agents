import pytest
from pydantic import ValidationError

from uk_job_market_agents.agents.classifier import ClassificationResult, classify_with_llm
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


def test_classify_with_llm_returns_structured_result(monkeypatch):
    expected = ClassificationResult(
        role_family=RoleFamily.DATA_SCIENCE,
        work_pattern=WorkPattern.HYBRID,
        reasoning=(
            "The role is focused on forecasting and optimisation, "
            "with mandatory office attendance twice per week."
        ),
    )

    def fake_model_call(title: str, description: str) -> ClassificationResult:
        return expected

    monkeypatch.setattr(
        "uk_job_market_agents.agents.classifier._call_model",
        fake_model_call,
    )

    result = classify_with_llm(
        "Data Scientist",
        (
            "This is a remote-first role. "
            "All team members must attend the Manchester office "
            "every Tuesday and Thursday."
        ),
    )

    assert result == expected
