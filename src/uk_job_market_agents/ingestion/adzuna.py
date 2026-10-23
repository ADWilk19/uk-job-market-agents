
"""Adapt Adzuna job advertisements to the internal JobPosting contract."""
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from uk_job_market_agents.models.job_posting import (
    DescriptionCompleteness,
    JobPosting,
)


def adapt_adzuna_job(
    payload: Mapping[str, Any],
    *,
    collected_at: datetime,
) -> JobPosting:
    """Convert an Adzuna advertisement into a validated JobPosting."""
    company = _optional_mapping(payload, "company")
    location = _optional_mapping(payload, "location")

    return JobPosting(
        source="adzuna",
        source_id=payload["id"],
        source_url=payload.get("redirect_url"),
        collected_at=collected_at,
        raw_title=payload["title"],
        raw_description=payload["description"],
        company_name=company.get("display_name"),
        location_raw=location.get("display_name"),
        description_completeness=DescriptionCompleteness.EXCERPT,
    )


def _optional_mapping(
    payload: Mapping[str, Any],
    field: str,
) -> Mapping[str, Any]:
    """Return optional nested metadata or reject malformed structures."""
    value = payload.get(field)

    if value is None:
        return {}

    if not isinstance(value, Mapping):
        raise ValueError(
            f"Adzuna field '{field}' must be a mapping or null"
        )

    return value
