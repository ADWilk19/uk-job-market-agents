import csv
from typing import TextIO

from uk_job_market_agents.analytics.batch_summary import BatchSummary


def write_batch_summary_csv(
    summary: BatchSummary,
    destination: TextIO,
) -> None:
    """Write a batch summary to a CSV text stream."""
    writer = csv.writer(destination, lineterminator="\n")

    writer.writerow(
        [
            "total",
            "processed",
            "review_required",
            "failed",
            "processed_rate",
            "review_rate",
            "failure_rate",
        ]
    )

    writer.writerow(
        [
            summary.total,
            summary.processed,
            summary.review_required,
            summary.failed,
            f"{summary.processed_rate:.6f}",
            f"{summary.review_rate:.6f}",
            f"{summary.failure_rate:.6f}",
        ]
    )
