import pytest
from pydantic import ValidationError

from uk_job_market_agents.agents.batch_orchestration import (
    BatchProcessingOutcome,
    ProcessingStatus,
)

from uk_job_market_agents.agents.orchestration import OrchestrationResult

from uk_job_market_agents.analytics import summary

from uk_job_market_agents.analytics.batch_summary import (
    BatchSummary,
    summarize_batch,
)


from uk_job_market_agents.agents.workflow import (
    ResolvedClassification,
    ReviewReason,
    WorkflowResolution,
)

from uk_job_market_agents.models.job_posting import (
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


def test_summarize_empty_batch():
    summary = summarize_batch([])

    assert summary.total == 0
    assert summary.processed == 0
    assert summary.review_required == 0
    assert summary.failed == 0


def test_summarize_batch_counts_failed_outcomes():
    outcomes = [
        BatchProcessingOutcome(
            job_id="job-001",
            status=ProcessingStatus.FAILED,
            error="LLM service unavailable",
        ),
        BatchProcessingOutcome(
            job_id="job-002",
            status=ProcessingStatus.FAILED,
            error="LLM request timed out",
        ),
    ]

    summary = summarize_batch(outcomes)

    assert summary.total == 2
    assert summary.processed == 0
    assert summary.review_required == 0
    assert summary.failed == 2

def test_summarize_batch_counts_mixed_outcomes():
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

    summary = summarize_batch(outcomes)

    assert summary.total == 3
    assert summary.processed == 1
    assert summary.review_required == 1
    assert summary.failed == 1
    assert summary.processed_rate == pytest.approx(1 / 3)
    assert summary.review_rate == pytest.approx(1 / 3)
    assert summary.failure_rate == pytest.approx(1 / 3)


def test_empty_batch_has_zero_rates():
    summary = summarize_batch([])

    assert summary.processed_rate == 0.0
    assert summary.review_rate == 0.0
    assert summary.failure_rate == 0.0


def test_batch_summary_rejects_inconsistent_counts():
    with pytest.raises(
        ValidationError,
        match="Status counts must sum to total",
    ):
        BatchSummary(
            total=10,
            processed=7,
            review_required=2,
            failed=3,
        )


@pytest.mark.parametrize(
    "field",
    ["total", "processed", "review_required", "failed"],
)
def test_batch_summary_rejects_negative_counts(field):
    counts = {
        "total": 0,
        "processed": 0,
        "review_required": 0,
        "failed": 0,
    }

    counts[field] = -1

    with pytest.raises(ValidationError):
        BatchSummary(**counts)
