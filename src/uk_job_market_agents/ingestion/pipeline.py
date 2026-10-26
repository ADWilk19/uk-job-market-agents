from collections.abc import Callable
from datetime import datetime
from typing import Any

from uk_job_market_agents.models.job_posting import JobPosting
from uk_job_market_agents.ingestion.deduplication import deduplicate_postings
from uk_job_market_agents.ingestion.adzuna import adapt_adzuna_job
from uk_job_market_agents.ingestion.adzuna_client import fetch_search_pages


def prepare_adzuna_postings(
    advertisements: list[dict[str, Any]],
    *,
    collected_at: datetime,
) -> list[JobPosting]:
    """Adapt and deduplicate Adzuna advertisements."""

    adapted_advertisements = [
        adapt_adzuna_job(
            advertisement,
            collected_at=collected_at,
        )
        for advertisement in advertisements
    ]

    unique_postings = deduplicate_postings(adapted_advertisements)

    return unique_postings


def ingest_adzuna_jobs(
    app_id: str,
    app_key: str,
    query: str,
    max_pages: int,
    *,
    collected_at: datetime,
    transport: Any,
    fetch_pages: Callable[..., list[dict[str, Any]]] = fetch_search_pages,
) -> list[JobPosting]:
    """Retrieve, adapt and deduplicate Adzuna advertisements."""

    raw_advertisements = fetch_pages(
        app_id=app_id,
        app_key=app_key,
        query=query,
        max_pages=max_pages,
        transport=transport,
    )

    unique_postings = prepare_adzuna_postings(
        raw_advertisements,
        collected_at=collected_at,
    )

    return unique_postings
