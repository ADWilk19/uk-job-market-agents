from uk_job_market_agents.agents.classifier import ClassificationResult
from uk_job_market_agents.evaluation.comparison import compare_classifiers
from uk_job_market_agents.models.job_posting import (
    RoleFamily,
    WorkPattern,
)


def test_compare_classifiers(monkeypatch):
    def fake_llm_classifier(
        title: str,
        description: str,
    ) -> ClassificationResult:
        return ClassificationResult(
            role_family=RoleFamily.DATA_SCIENCE,
            work_pattern=WorkPattern.HYBRID,
            reasoning="Mandatory office attendance twice per week.",
        )

    monkeypatch.setattr(
        "uk_job_market_agents.evaluation.comparison.classify_with_llm",
        fake_llm_classifier,
    )

    result = compare_classifiers(
        title="Data Scientist",
        description=(
            "This is a remote-first role. "
            "All team members must attend the Manchester office "
            "every Tuesday and Thursday."
        ),
        expected_role_family=RoleFamily.DATA_SCIENCE,
        expected_work_pattern=WorkPattern.HYBRID,
    )

    assert result.expected_role_family == RoleFamily.DATA_SCIENCE
    assert result.rules_role_family == RoleFamily.DATA_SCIENCE
    assert result.llm_role_family == RoleFamily.DATA_SCIENCE

    assert result.expected_work_pattern == WorkPattern.HYBRID
    assert result.rules_work_pattern == WorkPattern.REMOTE
    assert result.llm_work_pattern == WorkPattern.HYBRID
