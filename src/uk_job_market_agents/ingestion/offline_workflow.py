"""Compose prepared-posting processing and the existing CSV export contracts."""

from collections.abc import Callable
from pathlib import Path

from uk_job_market_agents.agents.batch_orchestration import BatchProcessingOutcome
from uk_job_market_agents.analytics.batch_output import write_batch_summary_csv
from uk_job_market_agents.analytics.batch_summary import BatchSummary
from uk_job_market_agents.analytics.job_export import build_job_export_rows
from uk_job_market_agents.analytics.job_export_csv import write_job_export_csv
from uk_job_market_agents.ingestion.batch_integration import run_postings_batch
from uk_job_market_agents.models.job_posting import JobPosting


def run_offline_workflow(
    postings: list[JobPosting],
    *,
    processor: Callable[[list[JobPosting]], list[BatchProcessingOutcome]],
    job_export_path: Path,
    summary_export_path: Path,
) -> tuple[list[BatchProcessingOutcome], BatchSummary]:
    """Process prepared postings and write both CSVs using an offline processor.

    Parents must exist. Existing files are overwritten; writes are not atomic.
    Pairing errors are raised before either export is opened. The caller is
    responsible for supplying a processor that does not make network calls.
    """
    if job_export_path.resolve() == summary_export_path.resolve() or (
        job_export_path.exists()
        and summary_export_path.exists()
        and job_export_path.samefile(summary_export_path)
    ):
        raise ValueError("Job and summary export paths must be distinct")

    outcomes, summary = run_postings_batch(postings, processor=processor)
    rows = build_job_export_rows(postings, outcomes)
    write_job_export_csv(rows, job_export_path)
    with summary_export_path.open("w", newline="", encoding="utf-8") as destination:
        write_batch_summary_csv(summary, destination)
    return outcomes, summary
