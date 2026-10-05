import pytest
from pydantic import ValidationError

from uk_job_market_agents.agents.classifier import ClassificationResult
from uk_job_market_agents.agents.workflow import (
    ClassificationWorkflowResult,
    ResolvedClassification,
    ReviewReason,
    WorkflowResolution,
    WorkPatternAdjudication,
    adjudicate_workflow,
    resolve_classification,
    run_classification_workflow,
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


def test_from_results_calculates_disagreement():
    llm_result = ClassificationResult(
        role_family=RoleFamily.DATA_SCIENCE,
        work_pattern=WorkPattern.HYBRID,
        reasoning="Mandatory office attendance twice per week.",
    )

    result = ClassificationWorkflowResult.from_results(
        rules_role_family=RoleFamily.DATA_SCIENCE,
        rules_work_pattern=WorkPattern.REMOTE,
        llm=llm_result,
    )

    assert result.role_family_agrees is True
    assert result.work_pattern_agrees is False


def test_from_results_calculates_full_agreement():
    llm_result = ClassificationResult(
        role_family=RoleFamily.DATA_ENGINEERING,
        work_pattern=WorkPattern.REMOTE,
        reasoning="The advert clearly describes remote data engineering work.",
    )

    result = ClassificationWorkflowResult.from_results(
        rules_role_family=RoleFamily.DATA_ENGINEERING,
        rules_work_pattern=WorkPattern.REMOTE,
        llm=llm_result,
    )

    assert result.role_family_agrees is True
    assert result.work_pattern_agrees is True


def test_run_classification_workflow(monkeypatch):
    expected_llm = ClassificationResult(
        role_family=RoleFamily.DATA_SCIENCE,
        work_pattern=WorkPattern.HYBRID,
        reasoning="Mandatory office attendance twice per week.",
    )

    def fake_classify_with_llm(
        title: str,
        description: str,
    ) -> ClassificationResult:
        return expected_llm

    monkeypatch.setattr(
        "uk_job_market_agents.agents.workflow.classify_with_llm",
        fake_classify_with_llm,
    )

    result = run_classification_workflow(
        "Data Scientist",
        (
            "This is a remote-first role. "
            "All team members must attend the Manchester office "
            "every Tuesday and Thursday."
        ),
    )

    assert result.rules_role_family == RoleFamily.DATA_SCIENCE
    assert result.rules_work_pattern == WorkPattern.REMOTE

    assert result.llm.role_family == RoleFamily.DATA_SCIENCE
    assert result.llm.work_pattern == WorkPattern.HYBRID

    assert result.role_family_agrees is True
    assert result.work_pattern_agrees is False


def test_resolve_classification_accepts_full_agreement():
    llm_result = ClassificationResult(
        role_family=RoleFamily.DATA_ENGINEERING,
        work_pattern=WorkPattern.REMOTE,
        reasoning="The role is clearly remote data engineering.",
    )

    workflow_result = ClassificationWorkflowResult.from_results(
        rules_role_family=RoleFamily.DATA_ENGINEERING,
        rules_work_pattern=WorkPattern.REMOTE,
        llm=llm_result,
    )

    resolution = resolve_classification(workflow_result)

    assert resolution.requires_review is False
    assert resolution.review_reason is None
    assert resolution.resolved == ResolvedClassification(
        role_family=RoleFamily.DATA_ENGINEERING,
        work_pattern=WorkPattern.REMOTE,
    )


def test_resolve_classification_escalates_disagreement():
    llm_result = ClassificationResult(
        role_family=RoleFamily.DATA_SCIENCE,
        work_pattern=WorkPattern.HYBRID,
        reasoning="Mandatory office attendance twice per week.",
    )

    workflow_result = ClassificationWorkflowResult.from_results(
        rules_role_family=RoleFamily.DATA_SCIENCE,
        rules_work_pattern=WorkPattern.REMOTE,
        llm=llm_result,
    )

    resolution = resolve_classification(workflow_result)

    assert resolution.requires_review is True
    assert resolution.resolved is None
    assert resolution.review_reason == ReviewReason.WORK_PATTERN


def test_resolve_classification_identifies_role_family_disagreement():
    llm_result = ClassificationResult(
        role_family=RoleFamily.ANALYTICS_ENGINEERING,
        work_pattern=WorkPattern.HYBRID,
        reasoning="The role is focused on analytics engineering.",
    )

    workflow_result = ClassificationWorkflowResult.from_results(
        rules_role_family=RoleFamily.DATA_ENGINEERING,
        rules_work_pattern=WorkPattern.HYBRID,
        llm=llm_result,
    )

    resolution = resolve_classification(workflow_result)

    assert resolution.requires_review is True
    assert resolution.review_reason == ReviewReason.ROLE_FAMILY


def test_resolve_classification_identifies_both_disagreements():
    llm_result = ClassificationResult(
        role_family=RoleFamily.ANALYTICS_ENGINEERING,
        work_pattern=WorkPattern.HYBRID,
        reasoning="Both role family and work pattern differ.",
    )

    workflow_result = ClassificationWorkflowResult.from_results(
        rules_role_family=RoleFamily.DATA_ENGINEERING,
        rules_work_pattern=WorkPattern.REMOTE,
        llm=llm_result,
    )

    resolution = resolve_classification(workflow_result)

    assert resolution.requires_review is True
    assert resolution.review_reason == ReviewReason.BOTH


def test_adjudicate_workflow_only_adjudicates_disputed_field(monkeypatch):
    workflow_result = ClassificationWorkflowResult.from_results(
        rules_role_family=RoleFamily.DATA_SCIENCE,
        rules_work_pattern=WorkPattern.REMOTE,
        llm=ClassificationResult(
            role_family=RoleFamily.DATA_SCIENCE,
            work_pattern=WorkPattern.HYBRID,
            reasoning="Mandatory office attendance twice per week.",
        ),
    )

    expected = WorkPatternAdjudication(
        rules_value=WorkPattern.REMOTE,
        llm_value=WorkPattern.HYBRID,
        recommended_value=WorkPattern.HYBRID,
        evidence=["Attendance is required every Tuesday and Thursday."],
        reasoning="Recurring mandatory attendance makes the role hybrid.",
    )

    monkeypatch.setattr(
        "uk_job_market_agents.agents.workflow.adjudicate_work_pattern",
        lambda **kwargs: expected,
    )

    result = adjudicate_workflow(
        title="Data Scientist",
        description="Remote-first, with mandatory office attendance twice per week.",
        result=workflow_result,
    )

    assert result.role_family_adjudication is None
    assert result.work_pattern_adjudication == expected


def test_adjudicate_workflow_skips_when_classifiers_agree():
    workflow_result = ClassificationWorkflowResult.from_results(
        rules_role_family=RoleFamily.DATA_ENGINEERING,
        rules_work_pattern=WorkPattern.REMOTE,
        llm=ClassificationResult(
            role_family=RoleFamily.DATA_ENGINEERING,
            work_pattern=WorkPattern.REMOTE,
            reasoning="Both classifiers agree.",
        ),
    )

    result = adjudicate_workflow(
        title="Data Engineer",
        description="Remote UK data engineering role.",
        result=workflow_result,
    )

    assert result.role_family_adjudication is None
    assert result.work_pattern_adjudication is None
