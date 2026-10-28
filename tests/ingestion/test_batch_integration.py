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
from uk_job_market_agents.ingestion.batch_integration import (
    run_postings_batch,
)
from uk_job_market_agents.ingestion.pipeline import (
    prepare_adzuna_postings,
)
from uk_job_market_agents.models.job_posting import (
    JobPosting,
    RoleFamily,
    WorkPattern,
)


def make_approved_result() -> OrchestrationResult:
    """Create an orchestration result with an approved classification."""
    resolution = WorkflowResolution(
        resolved=ResolvedClassification(
            role_family=RoleFamily.DATA_ENGINEERING,
            work_pattern=WorkPattern.HYBRID,
        ),
        requires_review=False,
        review_reason=None,
    )

    return OrchestrationResult(classification=resolution)


def make_review_result() -> OrchestrationResult:
    """Create an orchestration result requiring classification review."""
    resolution = WorkflowResolution(
        resolved=None,
        requires_review=True,
        review_reason=ReviewReason.ROLE_FAMILY,
    )

    return OrchestrationResult(classification=resolution)


def test_run_postings_batch_uses_injected_processor():
    posting = JobPosting(
        source="adzuna",
        source_id="123",
        raw_title="Data Engineer",
        raw_description="Python and SQL",
        collected_at=datetime(
            2026, 10, 28, tzinfo=timezone.utc
        ),
    )

    expected = [
        BatchProcessingOutcome(
            job_id="123",
            status=ProcessingStatus.FAILED,
            error="Simulated processing failure",
        )
    ]

    calls = []

    def fake_processor(postings):
        calls.append(postings)
        return expected

    outcomes, summary = run_postings_batch(
        [posting],
        processor=fake_processor,
    )

    assert calls == [[posting]]
    assert outcomes == expected
    assert summary.total == 1
    assert summary.failed == 1


def test_run_postings_batch_handles_empty_input():
    def fake_processor(postings):
        assert postings == []
        return []

    outcomes, summary = run_postings_batch(
        [],
        processor=fake_processor,
    )

    assert outcomes == []
    assert summary.total == 0
    assert summary.failed == 0


def test_run_postings_batch_summarizes_mixed_outcomes():
    outcomes = [
        BatchProcessingOutcome(
            job_id="job-001",
            status=ProcessingStatus.PROCESSED,
            result=make_approved_result(),
        ),
        BatchProcessingOutcome(
            job_id="job-002",
            status=ProcessingStatus.REVIEW_REQUIRED,
            result=make_review_result(),
        ),
        BatchProcessingOutcome(
            job_id="job-003",
            status=ProcessingStatus.FAILED,
            error="LLM service unavailable",
        ),
    ]

    received_postings = []

    def fake_processor(postings):
        received_postings.extend(postings)
        return outcomes

    returned_outcomes, summary = run_postings_batch(
        [],
        processor=fake_processor,
    )

    assert received_postings == []
    assert returned_outcomes == outcomes

    assert summary.total == 3
    assert summary.processed == 1
    assert summary.review_required == 1
    assert summary.failed == 1

    assert summary.processed_rate == pytest.approx(1 / 3)
    assert summary.review_rate == pytest.approx(1 / 3)
    assert summary.failure_rate == pytest.approx(1 / 3)


def test_adzuna_postings_flow_into_batch_processing():
    advertisements = [
        {
            "id": "job-001",
            "title": "Data Engineer",
            "description": "Python and SQL",
        },
        {
            "id": "job-002",
            "title": "Analytics Engineer",
            "description": "Data modelling and reporting",
        },
    ]

    advertisements.append(advertisements[0].copy())

    collected_at = datetime(
        2026, 10, 28, tzinfo=timezone.utc
    )

    postings = prepare_adzuna_postings(
        advertisements,
        collected_at=collected_at,
    )

    received_postings = []

    def fake_processor(jobs):
        received_postings.extend(jobs)

        return [
            BatchProcessingOutcome(
                job_id=job.source_id,
                status=ProcessingStatus.FAILED,
                error="Simulated processing failure",
            )
            for job in jobs
        ]

    outcomes, summary = run_postings_batch(
        postings,
        processor=fake_processor,
    )

    assert len(advertisements) == 3
    assert len(postings) == 2
    assert len(received_postings) == 2

    assert [job.source_id for job in postings] == [
        "job-001",
        "job-002",
    ]

    assert all(job.source == "adzuna" for job in postings)
    assert all(job.collected_at == collected_at for job in postings)

    assert len(outcomes) == 2
    assert summary.total == 2
    assert summary.failed == 2
