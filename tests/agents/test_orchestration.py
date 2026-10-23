from datetime import datetime, timezone
from unittest.mock import patch

from uk_job_market_agents.agents.classifier import ClassificationResult

from uk_job_market_agents.agents.orchestration import (
    OrchestrationResult,
    process_job
)

from uk_job_market_agents.agents.salary_extractor import SalaryExtractionResult

from uk_job_market_agents.agents.salary_review import (
    SalaryAssessment,
    SalaryReviewStatus,
)

from uk_job_market_agents.agents.workflow import (
    WorkflowResolution,
    ReviewReason,
    ClassificationWorkflowResult,
)

from uk_job_market_agents.models.job_posting import (
    DescriptionCompleteness,
    JobPosting,
    RoleFamily,
    WorkPattern,
)


def test_orchestration_result_preserves_review_status():
    resolution = WorkflowResolution(
        resolved=None,
        requires_review=True,
        review_reason=ReviewReason.ROLE_FAMILY,
    )

    result = OrchestrationResult(
        classification=resolution,
    )

    assert result.classification.requires_review is True
    assert result.classification.review_reason == ReviewReason.ROLE_FAMILY
    assert result.analytical_record is None


def test_process_job_builds_approved_analytical_record():
    job = JobPosting(
        source_id="job-001",
        source="example",
        collected_at=datetime.now(timezone.utc),
        raw_title="Senior Data Engineer",
        raw_description="Python, SQL and dbt. Hybrid working.",
        company_name="Example Analytics Ltd",
        location_raw="Southampton, Hampshire",
        description_completeness=DescriptionCompleteness.EXCERPT,
    )

    classification = ClassificationWorkflowResult.from_results(
        rules_role_family=RoleFamily.DATA_ENGINEERING,
        rules_work_pattern=WorkPattern.HYBRID,
        llm=ClassificationResult(
            role_family=RoleFamily.DATA_ENGINEERING,
            work_pattern=WorkPattern.HYBRID,
            reasoning="The advertisement describes a hybrid data engineering role.",
        ),
    )

    assessment = SalaryAssessment(
        extraction=SalaryExtractionResult(
            salary=None,
            evidence=None,
        ),
        status=SalaryReviewStatus.NOT_DISCLOSED,
    )

    with (
        patch(
            "uk_job_market_agents.agents.orchestration.run_classification_workflow",
            return_value=classification,
        ),
        patch(
            "uk_job_market_agents.agents.orchestration.run_salary_workflow",
            return_value=assessment,
        ) as mock_salary,
    ):
        result = process_job(job)

    mock_salary.assert_called_once_with(job.raw_description)

    assert result.classification.requires_review is False

    assert result.analytical_record is not None
    assert result.analytical_record.title == "Senior Data Engineer"
    assert result.analytical_record.company_name == "Example Analytics Ltd"
    assert result.analytical_record.location_raw == "Southampton, Hampshire"

    assert result.analytical_record.role_family == RoleFamily.DATA_ENGINEERING
    assert result.analytical_record.work_pattern == WorkPattern.HYBRID

    assert result.analytical_record.salary_min is None
    assert result.analytical_record.salary_max is None

    # Source provenance survives successful orchestration.
    assert result.source_id == job.source_id
    assert result.source == job.source
    assert result.source_url == job.source_url
    assert result.collected_at == job.collected_at
    assert (
        result.description_completeness
        == DescriptionCompleteness.EXCERPT
    )



def test_process_job_excludes_classification_requiring_review():
    job = JobPosting(
        source_id="job-002",
        source="example",
        collected_at=datetime.now(timezone.utc),
        raw_title="Senior Data Engineer",
        raw_description="Python, SQL and dbt. Hybrid working.",
        company_name="Example Analytics Ltd",
        location_raw="Southampton, Hampshire",
    )

    classification = ClassificationWorkflowResult.from_results(
        rules_role_family=RoleFamily.DATA_ENGINEERING,
        rules_work_pattern=WorkPattern.HYBRID,
        llm=ClassificationResult(
            role_family=RoleFamily.DATA_SCIENCE,
            work_pattern=WorkPattern.HYBRID,
            reasoning="The advertisement describes analytical modelling.",
        ),
    )

    with (
        patch(
            "uk_job_market_agents.agents.orchestration.run_classification_workflow",
            return_value=classification,
        ),
        patch(
            "uk_job_market_agents.agents.orchestration.run_salary_workflow",
        ) as mock_salary,
    ):
        result = process_job(job)

    mock_salary.assert_not_called()

    assert result.classification.requires_review is True
    assert result.classification.review_reason == ReviewReason.ROLE_FAMILY
    assert result.classification.resolved is None

    assert result.analytical_record is None

    assert result.salary_assessment is None


def test_process_job_includes_verified_annual_salary():
    job = JobPosting(
        source_id="job-003",
        source="example",
        collected_at=datetime.now(timezone.utc),
        raw_title="Senior Data Engineer",
        raw_description=(
            "Python, SQL and dbt. Hybrid working. "
            "Salary: £60,000–£80,000 per annum."
        ),
        company_name="Example Analytics Ltd",
        location_raw="Southampton, Hampshire",
    )

    classification = ClassificationWorkflowResult.from_results(
        rules_role_family=RoleFamily.DATA_ENGINEERING,
        rules_work_pattern=WorkPattern.HYBRID,
        llm=ClassificationResult(
            role_family=RoleFamily.DATA_ENGINEERING,
            work_pattern=WorkPattern.HYBRID,
            reasoning="The role involves data engineering and hybrid working.",
        ),
    )

    assessment = SalaryAssessment(
        extraction=SalaryExtractionResult(
            salary={
                "salary_min": 60000,
                "salary_max": 80000,
                "period": "year",
                "currency": "GBP",
            },
            evidence="£60,000–£80,000 per annum",
        ),
        status=SalaryReviewStatus.VERIFIED,
    )

    with (
        patch(
            "uk_job_market_agents.agents.orchestration.run_classification_workflow",
            return_value=classification,
        ),
        patch(
            "uk_job_market_agents.agents.orchestration.run_salary_workflow",
            return_value=assessment,
        ) as mock_salary,
    ):
        result = process_job(job)

    mock_salary.assert_called_once_with(job.raw_description)

    assert result.classification.requires_review is False
    assert result.salary_assessment is not None
    assert result.salary_assessment.status == SalaryReviewStatus.VERIFIED

    assert result.analytical_record is not None
    assert result.analytical_record.salary_min == 60000
    assert result.analytical_record.salary_max == 80000
    assert result.analytical_record.salary_midpoint == 70000.0

    assert result.analytical_record.company_name == "Example Analytics Ltd"
    assert result.analytical_record.location_raw == "Southampton, Hampshire"


def test_process_job_excludes_unverified_salary():
    job = JobPosting(
        source_id="job-004",
        source="example",
        collected_at=datetime.now(timezone.utc),
        raw_title="Senior Data Engineer",
        raw_description=(
            "Python, SQL and dbt. Hybrid working. "
            "Salary: £60,000–£80,000 per annum."
        ),
        company_name="Example Analytics Ltd",
        location_raw="Southampton, Hampshire",
    )

    classification = ClassificationWorkflowResult.from_results(
        rules_role_family=RoleFamily.DATA_ENGINEERING,
        rules_work_pattern=WorkPattern.HYBRID,
        llm=ClassificationResult(
            role_family=RoleFamily.DATA_ENGINEERING,
            work_pattern=WorkPattern.HYBRID,
            reasoning="The role involves data engineering and hybrid working.",
        ),
    )

    assessment = SalaryAssessment(
        extraction=SalaryExtractionResult(
            salary={
                "salary_min": 600000,
                "salary_max": 800000,
                "period": "year",
                "currency": "GBP",
            },
            evidence="£60,000–£80,000 per annum",
        ),
        status=SalaryReviewStatus.REVIEW_REQUIRED,
        reason="Extracted salary values disagree with evidence",
    )

    with (
        patch(
            "uk_job_market_agents.agents.orchestration.run_classification_workflow",
            return_value=classification,
        ),
        patch(
            "uk_job_market_agents.agents.orchestration.run_salary_workflow",
            return_value=assessment,
        ) as mock_salary,
    ):
        result = process_job(job)

    mock_salary.assert_called_once_with(job.raw_description)

    # Classification remains approved.
    assert result.classification.requires_review is False

    # The job remains available for analysis.
    assert result.analytical_record is not None
    assert result.analytical_record.role_family == RoleFamily.DATA_ENGINEERING
    assert result.analytical_record.company_name == "Example Analytics Ltd"

    # Unverified salary information must not enter analytics.
    assert result.analytical_record.salary_min is None
    assert result.analytical_record.salary_max is None
    assert result.analytical_record.salary_midpoint is None

    # The reason for rejecting the salary remains auditable.
    assert result.salary_assessment is not None
    assert result.salary_assessment.status == SalaryReviewStatus.REVIEW_REQUIRED
    assert (
        result.salary_assessment.reason
        == "Extracted salary values disagree with evidence"
    )


def test_orchestration_preserves_source_provenance(monkeypatch):
    job = JobPosting(
        source_id="adzuna-12345",
        source="adzuna",
        source_url="https://www.adzuna.co.uk/jobs/details/12345",
        collected_at=datetime(
            2026, 10, 23, 8, 0, tzinfo=timezone.utc
        ),
        raw_title="Data Engineer",
        raw_description="Python and SQL",
        description_completeness=DescriptionCompleteness.EXCERPT,
    )

    # Avoid real agent/API calls in this contract test.
    monkeypatch.setattr(
        "uk_job_market_agents.agents.orchestration.run_classification_workflow",
        lambda **kwargs: object(),
    )


    monkeypatch.setattr(
        "uk_job_market_agents.agents.orchestration.resolve_classification",
        lambda workflow: WorkflowResolution(
            resolved=None,
            requires_review=True,
            review_reason=ReviewReason.ROLE_FAMILY,
        ),
    )


    result = process_job(job)

    assert result.source_id == job.source_id
    assert result.source == job.source
    assert result.source_url == job.source_url
    assert result.collected_at == job.collected_at
    assert (
        result.description_completeness
        == DescriptionCompleteness.EXCERPT
    )
