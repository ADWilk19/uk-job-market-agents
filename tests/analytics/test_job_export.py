import pytest
from datetime import datetime, timezone

from uk_job_market_agents.agents.batch_orchestration import (
    BatchProcessingOutcome,
    ProcessingStatus,
)
from uk_job_market_agents.agents.orchestration import OrchestrationResult
from uk_job_market_agents.agents.workflow import (
    ResolvedClassification,
    ReviewReason,
    WorkflowResolution,
)
from uk_job_market_agents.analytics.job_export import (
    build_job_export_rows,
)
from uk_job_market_agents.analytics.models import AnalyticalJobRecord
from uk_job_market_agents.models.job_posting import (
    JobPosting,
    DescriptionCompleteness,
    RoleFamily,
    WorkPattern,
)


def test_failed_job_preserves_source_provenance():
    posting = JobPosting(
        source="adzuna",
        source_id="job-001",
        raw_title="Data Engineer",
        raw_description="Python and SQL",
        collected_at=datetime(
            2026, 10, 29, tzinfo=timezone.utc
        ),
        description_completeness=DescriptionCompleteness.EXCERPT,
        source_salary_min=40000.0,
        source_salary_max=50000.0,
        source_salary_predicted=True,
    )

    outcome = BatchProcessingOutcome(
        job_id="job-001",
        status=ProcessingStatus.FAILED,
        error="Simulated processing failure",
    )

    rows = build_job_export_rows([posting], [outcome])

    assert len(rows) == 1

    row = rows[0]

    assert row.collected_at == posting.collected_at
    assert row.source_salary_min == 40000.0
    assert row.source_salary_max == 50000.0
    assert row.source == "adzuna"
    assert row.source_id == "job-001"
    assert row.processing_status == ProcessingStatus.FAILED
    assert row.description_completeness == DescriptionCompleteness.EXCERPT
    assert row.salary_min is None
    assert row.source_salary_predicted is True


def test_export_rejects_mismatched_lengths():
    with pytest.raises(ValueError):
        build_job_export_rows([], [
            BatchProcessingOutcome(
                job_id="job-001",
                status=ProcessingStatus.FAILED,
                error="Simulated failure",
            )
        ])


def test_export_rejects_mismatched_identifiers():
    posting = JobPosting(
        source="adzuna",
        source_id="job-001",
        raw_title="Data Engineer",
        raw_description="Python and SQL",
        collected_at=datetime(2026, 10, 29, tzinfo=timezone.utc),
    )

    outcome = BatchProcessingOutcome(
        job_id="job-999",
        status=ProcessingStatus.FAILED,
        error="Simulated failure",
    )

    with pytest.raises(ValueError, match="identifiers do not match"):
        build_job_export_rows([posting], [outcome])


def test_approved_job_exports_analytical_values():
    posting = JobPosting(
        source="adzuna",
        source_id="job-002",
        raw_title="Data Engineer",
        raw_description="Hybrid role paying £45,000–£55,000",
        collected_at=datetime(
            2026, 10, 29, tzinfo=timezone.utc
        ),
    )

    resolution = WorkflowResolution(
        resolved=ResolvedClassification(
            role_family=RoleFamily.DATA_ENGINEERING,
            work_pattern=WorkPattern.HYBRID,
        ),
        requires_review=False,
        review_reason=None,
    )

    analytical_record = AnalyticalJobRecord(
        title="Data Engineer",
        role_family=RoleFamily.DATA_ENGINEERING,
        work_pattern=WorkPattern.HYBRID,
        salary_min=45000,
        salary_max=55000,
    )

    result = OrchestrationResult(
        classification=resolution,
        analytical_record=analytical_record,
    )

    outcome = BatchProcessingOutcome(
        job_id="job-002",
        status=ProcessingStatus.PROCESSED,
        result=result,
    )

    rows = build_job_export_rows([posting], [outcome])

    assert len(rows) == 1

    row = rows[0]

    assert row.processing_status == ProcessingStatus.PROCESSED
    assert row.role_family == RoleFamily.DATA_ENGINEERING
    assert row.work_pattern == WorkPattern.HYBRID
    assert row.salary_min == 45000
    assert row.salary_max == 55000


@pytest.mark.parametrize("has_analytical_record", [False, True])
def test_review_required_job_preserves_provenance_without_analytical_values(
    has_analytical_record,
):
    posting = JobPosting(
        source="adzuna",
        source_id="job-003",
        raw_title="Data Specialist",
        raw_description="Flexible working arrangements",
        collected_at=datetime(
            2026, 10, 29, tzinfo=timezone.utc
        ),
    )

    resolution = WorkflowResolution(
        resolved=None,
        requires_review=True,
        review_reason=ReviewReason.ROLE_FAMILY,
    )

    outcome = BatchProcessingOutcome(
        job_id="job-003",
        status=ProcessingStatus.REVIEW_REQUIRED,
        result=OrchestrationResult(
            classification=resolution,
            analytical_record=(
                AnalyticalJobRecord(
                    title="Unapproved record",
                    role_family=RoleFamily.DATA_ENGINEERING,
                    work_pattern=WorkPattern.HYBRID,
                    salary_min=45000,
                    salary_max=55000,
                )
                if has_analytical_record else None
            ),
        ),
    )

    rows = build_job_export_rows([posting], [outcome])

    assert len(rows) == 1

    row = rows[0]

    assert row.source_id == "job-003"
    assert row.processing_status == ProcessingStatus.REVIEW_REQUIRED
    assert row.role_family is None
    assert row.work_pattern is None
    assert row.salary_min is None
    assert row.salary_max is None
    assert row.classification_review_reason == ReviewReason.ROLE_FAMILY


def test_failed_outcome_with_provider_salary_metadata():
    posting = JobPosting(
            source="adzuna",
            source_id="job-003",
            raw_title="Data Specialist",
            raw_description="Flexible working arrangements",
            collected_at=datetime(
                2026, 10, 29, tzinfo=timezone.utc
            ),
            source_salary_min=40000.00,
            source_salary_max=60000.00,
        )

    outcome = BatchProcessingOutcome(
        job_id="job-003",
        status=ProcessingStatus.FAILED,
        error="Simulated processing failure"
    )

    rows = build_job_export_rows([posting], [outcome])

    row = rows[0]

    assert row.source_salary_min == 40000.00
    assert row.source_salary_max == 60000.00
    assert row.salary_min is None
    assert row.salary_max is None


def test_processed_job_without_verified_salary():
    posting = JobPosting(
            source="adzuna",
            source_id="job-004",
            raw_title="Data Engineer",
            raw_description="Hybrid role requiring Python and SQL",
            collected_at=datetime(
                2026, 10, 29, tzinfo=timezone.utc
            ),
            source_salary_min=45000.0,
            source_salary_max=55000.0,
            source_salary_predicted=True,
        )

    resolution = WorkflowResolution(
        resolved=ResolvedClassification(
            role_family=RoleFamily.DATA_ENGINEERING,
            work_pattern=WorkPattern.HYBRID,
        ),
        requires_review=False,
        review_reason=None,
    )

    analytical_record = AnalyticalJobRecord(
        title="Data Engineer",
        role_family=RoleFamily.DATA_ENGINEERING,
        work_pattern=WorkPattern.HYBRID,
    )

    result = OrchestrationResult(
        classification=resolution,
        analytical_record=analytical_record,
    )

    outcome = BatchProcessingOutcome(
        job_id="job-004",
        status=ProcessingStatus.PROCESSED,
        result=result,
    )

    rows = build_job_export_rows([posting], [outcome])

    row = rows[0]

    assert row.source_salary_min == 45000.0
    assert row.source_salary_max == 55000.0
    assert row.salary_min is None
    assert row.salary_max is None

    assert row.processing_status == ProcessingStatus.PROCESSED
    assert row.role_family == RoleFamily.DATA_ENGINEERING
    assert row.work_pattern == WorkPattern.HYBRID
