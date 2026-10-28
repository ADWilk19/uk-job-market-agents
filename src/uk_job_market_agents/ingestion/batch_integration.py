from uk_job_market_agents.agents.batch_orchestration import (
    BatchProcessingOutcome,
    process_jobs,
)
from uk_job_market_agents.analytics.batch_summary import (
    BatchSummary,
    summarize_batch
)
from uk_job_market_agents.models.job_posting import JobPosting


def run_postings_batch(
    postings: list[JobPosting],
    *,
    processor=process_jobs,
) -> tuple[list[BatchProcessingOutcome], BatchSummary]:
        """Process a batch of postings and summarize the outcomes."""
        outcomes = processor(postings)
        summary = summarize_batch(outcomes)

        return outcomes, summary
