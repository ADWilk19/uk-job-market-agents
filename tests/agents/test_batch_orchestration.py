from datetime import datetime
from unittest.mock import call, patch

import pytest
from pydantic import ValidationError

from uk_job_market_agents.agents.batch_orchestration import (
    process_jobs,
    BatchProcessingOutcome,
    ProcessingStatus,
)

from uk_job_market_agents.agents.orchestration import OrchestrationResult

from uk_job_market_agents.agents.workflow import (
    ResolvedClassification,
    ReviewReason,
    WorkflowResolution,
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


def test_process_jobs_returns_empty_list_for_empty_batch():
    assert process_jobs([]) == []


def test_process_jobs_processes_each_advertisement_in_order():
    jobs = [
        JobPosting(
            source_id=f"job-{i:03d}",
            source="example",
            collected_at=datetime.now(),
            raw_title="Data Engineer",
            raw_description="Python and SQL. Remote working.",
        )
        for i in range(1, 3)
    ]

    with patch(
        "uk_job_market_agents.agents.batch_orchestration.process_job"
    ) as mock_process_job:
        first_result = make_approved_result()
        second_result = make_review_result()

        mock_process_job.side_effect = [first_result, second_result]

        results = process_jobs(jobs)

    assert [outcome.job_id for outcome in results] == [
    "job-001",
    "job-002",
]

    assert [outcome.status for outcome in results] == [
        ProcessingStatus.PROCESSED,
        ProcessingStatus.REVIEW_REQUIRED,
    ]

    assert results[0].result == first_result
    assert results[1].result == second_result
    assert mock_process_job.call_args_list == [
        call(jobs[0]),
        call(jobs[1]),
    ]


def test_batch_outcome_preserves_failure_information():
    outcome = BatchProcessingOutcome(
        job_id="job-123",
        status=ProcessingStatus.FAILED,
        error="LLM service unavailable",
    )

    assert outcome.job_id == "job-123"
    assert outcome.status == ProcessingStatus.FAILED
    assert outcome.result is None
    assert outcome.error == "LLM service unavailable"


def test_failed_outcome_requires_error_message():
    with pytest.raises(ValidationError):
        BatchProcessingOutcome(
            job_id="job-123",
            status=ProcessingStatus.FAILED,
        )


def test_failed_outcome_rejects_result():
    with pytest.raises(
        ValidationError,
        match="Failed outcomes must not include a result",
    ):
        BatchProcessingOutcome(
            job_id="job-123",
            status=ProcessingStatus.FAILED,
            result=make_approved_result(),
            error="LLM service unavailable",
        )


@pytest.mark.parametrize("error", [None, "", "   ", "\t\n"])
def test_failed_outcome_requires_meaningful_error(error):
    with pytest.raises(
        ValidationError,
        match="Failed outcomes must include a non-empty error message",
    ):
        BatchProcessingOutcome(
            job_id="job-123",
            status=ProcessingStatus.FAILED,
            error=error,
        )


def test_processed_outcome_requires_result():
    with pytest.raises(
        ValidationError,
        match="Processed outcomes must include a result",
    ):
        BatchProcessingOutcome(
            job_id="job-123",
            status=ProcessingStatus.PROCESSED,
        )


def test_review_required_outcome_requires_result():
    with pytest.raises(
        ValidationError,
        match="Review-required outcomes must include a result",
    ):
        BatchProcessingOutcome(
            job_id="job-123",
            status=ProcessingStatus.REVIEW_REQUIRED,
        )


def test_processed_outcome_accepts_approved_classification():
    outcome = BatchProcessingOutcome(
        job_id="job-001",
        status=ProcessingStatus.PROCESSED,
        result=make_approved_result(),
    )

    assert outcome.status == ProcessingStatus.PROCESSED
    assert outcome.result is not None
    assert outcome.result.classification.requires_review is False


def test_review_outcome_accepts_review_required_classification():
    outcome = BatchProcessingOutcome(
        job_id="job-002",
        status=ProcessingStatus.REVIEW_REQUIRED,
        result=make_review_result(),
    )

    assert outcome.status == ProcessingStatus.REVIEW_REQUIRED
    assert outcome.result is not None
    assert outcome.result.classification.requires_review is True


def test_processed_outcome_rejects_review_required_classification():
    with pytest.raises(
        ValidationError,
        match="Processed outcomes must not require classification review",
    ):
        BatchProcessingOutcome(
            job_id="job-003",
            status=ProcessingStatus.PROCESSED,
            result=make_review_result(),
        )


def test_review_outcome_rejects_approved_classification():
    with pytest.raises(
        ValidationError,
        match="Review-required outcomes must contain a classification requiring review",
    ):
        BatchProcessingOutcome(
            job_id="job-004",
            status=ProcessingStatus.REVIEW_REQUIRED,
            result=make_approved_result(),
        )


def test_process_jobs_continues_after_failure():
    jobs = [
            JobPosting(
                source_id=f"job-{i:03d}",
                source="example",
                collected_at=datetime.now(),
                raw_title="Data Engineer",
                raw_description="Python and SQL. Remote working.",
            )
            for i in range(1, 4)
        ]

    with patch(
        "uk_job_market_agents.agents.batch_orchestration.process_job"
    ) as mock_process_job:
        mock_process_job.side_effect = [
            make_approved_result(),
            RuntimeError("LLM service unavailable"),
            make_approved_result(),
        ]

        outcomes = process_jobs(jobs)

    assert len(outcomes) == 3
    assert outcomes[0].status == ProcessingStatus.PROCESSED
    assert outcomes[1].status == ProcessingStatus.FAILED
    assert outcomes[2].status == ProcessingStatus.PROCESSED

    assert mock_process_job.call_count == 3


def test_process_jobs_preserves_mixed_processing_outcomes():
    jobs = [
        JobPosting(
            source_id=f"job-{i:03d}",
            source="example",
            collected_at=datetime.now(),
            raw_title="Data Engineer",
            raw_description="Python and SQL. Remote working.",
        )
        for i in range(1, 5)
    ]

    with patch(
        "uk_job_market_agents.agents.batch_orchestration.process_job"
    ) as mock_process_job:
        mock_process_job.side_effect = [
            make_approved_result(),
            make_review_result(),
            RuntimeError("LLM service unavailable"),
            make_approved_result(),
        ]

        outcomes = process_jobs(jobs)

    assert mock_process_job.call_count == 4

    assert [outcome.job_id for outcome in outcomes] == [
        "job-001",
        "job-002",
        "job-003",
        "job-004",
    ]

    assert outcomes[2].result is None
    assert outcomes[2].error == "LLM service unavailable"

    assert [outcome.status for outcome in outcomes] == [
        ProcessingStatus.PROCESSED,
        ProcessingStatus.REVIEW_REQUIRED,
        ProcessingStatus.FAILED,
        ProcessingStatus.PROCESSED,
    ]


@pytest.mark.parametrize(
    ("status", "result", "message"),
    [
        (
            ProcessingStatus.PROCESSED,
            make_approved_result(),
            "Processed outcomes must not include an error message",
        ),
        (
            ProcessingStatus.REVIEW_REQUIRED,
            make_review_result(),
            "Review-required outcomes must not include an error message",
        ),
    ],
)
def test_non_failed_outcomes_reject_error_messages(status, result, message):
    with pytest.raises(ValidationError, match=message):
        BatchProcessingOutcome(
            job_id="job-123",
            status=status,
            result=result,
            error="Unexpected error",
        )
