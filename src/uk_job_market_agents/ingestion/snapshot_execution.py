"""Execute saved Adzuna snapshots through the offline workflow."""

from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from uk_job_market_agents.agents.batch_orchestration import (
    BatchProcessingOutcome,
)
from uk_job_market_agents.analytics.batch_summary import BatchSummary
from uk_job_market_agents.ingestion.offline_workflow import (
    run_offline_workflow,
)
from uk_job_market_agents.ingestion.snapshot_pipeline import (
    prepare_adzuna_snapshot,
)
from uk_job_market_agents.models.job_posting import JobPosting


def run_snapshot_workflow(
    snapshot_path: Path,
    *,
    collected_at: datetime,
    processor: Callable[
        [list[JobPosting]],
        list[BatchProcessingOutcome],
    ],
    job_export_path: Path,
    summary_export_path: Path,
) -> tuple[list[BatchProcessingOutcome], BatchSummary]:
    """Process a saved snapshot and write the existing CSV exports."""
    postings = prepare_adzuna_snapshot(
        snapshot_path,
        collected_at=collected_at,
    )

    return run_offline_workflow(
        postings,
        processor=processor,
        job_export_path=job_export_path,
        summary_export_path=summary_export_path,
    )
