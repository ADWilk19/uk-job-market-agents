from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from uk_job_market_agents.agents.batch_orchestration import (
    BatchProcessingOutcome,
    ProcessingStatus,
)


class BatchSummary(BaseModel):
    """Represent aggregate processing counts for a batch."""

    total: int = Field(ge=0)
    processed: int = Field(ge=0)
    review_required: int = Field(ge=0)
    failed: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_counts(self) -> BatchSummary:
        """Ensure processing status counts equal the batch total."""
        status_total = self.processed + self.review_required + self.failed

        if status_total != self.total:
            raise ValueError(
                "Status counts must sum to total"
            )

        return self

    @property
    def processed_rate(self) -> float:
        """Return the proportion of successfully processed advertisements."""
        if self.total == 0:
            return 0.0

        return self.processed / self.total

    @property
    def review_rate(self) -> float:
        """Return the proportion of advertisements requiring review."""
        if self.total == 0:
            return 0.0

        return self.review_required / self.total

    @property
    def failure_rate(self) -> float:
        """Return the proportion of failed advertisements."""
        if self.total == 0:
            return 0.0

        return self.failed / self.total


def summarize_batch(outcomes: list[BatchProcessingOutcome]) -> BatchSummary:
    """Summarize the processing outcomes of a batch."""

    processed_count = 0
    review_count = 0
    failed_count = 0

    for outcome in outcomes:
        if outcome.status == ProcessingStatus.PROCESSED:
            processed_count += 1
        elif outcome.status == ProcessingStatus.REVIEW_REQUIRED:
            review_count += 1
        elif outcome.status == ProcessingStatus.FAILED:
            failed_count += 1

    return BatchSummary(
        total=len(outcomes),
        processed=processed_count,
        review_required=review_count,
        failed=failed_count,
    )
