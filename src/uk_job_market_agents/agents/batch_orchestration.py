from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, model_validator

from uk_job_market_agents.agents.orchestration import (
    OrchestrationResult,
    process_job,
)

from uk_job_market_agents.models.job_posting import JobPosting


class ProcessingStatus(str, Enum):
    PROCESSED = "processed"
    REVIEW_REQUIRED = "review_required"
    FAILED = "failed"


class BatchProcessingOutcome(BaseModel):
    """Represent the processing outcome of an individual job advertisement."""

    job_id: str
    result: OrchestrationResult | None = None
    status: ProcessingStatus
    error: str | None = None

    @model_validator(mode="after")
    def validate_outcome(self) -> BatchProcessingOutcome:
        """Ensure processing outcomes contain consistent information."""

        if self.status == ProcessingStatus.FAILED:
            if not self.error or not self.error.strip():
                raise ValueError(
                    "Failed outcomes must include a non-empty error message"
                )

            if self.result is not None:
                raise ValueError(
                    "Failed outcomes must not include a result"
                )

        elif self.status == ProcessingStatus.PROCESSED:
            if self.result is None:
                raise ValueError(
                    "Processed outcomes must include a result"
                )

            if self.error is not None:
                raise ValueError(
                    "Processed outcomes must not include an error message"
                )

            if self.result.classification.requires_review:
                raise ValueError(
                    "Processed outcomes must not require classification review"
                )

        elif self.status == ProcessingStatus.REVIEW_REQUIRED:
            if self.result is None:
                raise ValueError(
                    "Review-required outcomes must include a result"
                )

            if self.error is not None:
                raise ValueError(
                    "Review-required outcomes must not include an error message"
                )

            if not self.result.classification.requires_review:
                raise ValueError(
                    "Review-required outcomes must contain a classification requiring review"
                )

        return self


def process_jobs(jobs: list[JobPosting]) -> list[BatchProcessingOutcome]:
    """Process a batch of job advertisements."""
    outcomes: list[BatchProcessingOutcome] = []

    for job in jobs:
        try:
            result = process_job(job)

            processing_status = (
                ProcessingStatus.REVIEW_REQUIRED
                if result.classification.requires_review
                else ProcessingStatus.PROCESSED
            )

            outcome = BatchProcessingOutcome(
                job_id=job.source_id,
                result=result,
                status=processing_status,
            )
        except Exception as exc:
            outcome = BatchProcessingOutcome(
                job_id=job.source_id,
                status=ProcessingStatus.FAILED,
                error=str(exc).strip() or type(exc).__name__,
            )

        outcomes.append(outcome)

    return outcomes
