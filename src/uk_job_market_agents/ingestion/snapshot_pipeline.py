"""Prepare saved Adzuna snapshots for offline processing."""

from datetime import datetime
from pathlib import Path

from uk_job_market_agents.ingestion.pipeline import (
    prepare_adzuna_postings,
)
from uk_job_market_agents.ingestion.snapshot_loader import (
    load_adzuna_snapshot,
)
from uk_job_market_agents.models.job_posting import JobPosting


def prepare_adzuna_snapshot(
    path: Path,
    *,
    collected_at: datetime,
) -> list[JobPosting]:
    """Load, adapt and deduplicate advertisements from a saved snapshot."""
    advertisements = load_adzuna_snapshot(path)

    return prepare_adzuna_postings(
        advertisements,
        collected_at=collected_at,
    )
