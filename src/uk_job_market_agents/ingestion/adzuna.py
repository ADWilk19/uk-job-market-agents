
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
    category = _optional_mapping(payload, "category")

    return JobPosting(
        source="adzuna",
        source_id=payload["id"],
        source_url=payload.get("redirect_url"),
        collected_at=collected_at,
        published_at=payload.get("created"),
        raw_title=payload["title"],
        raw_description=payload["description"],
        company_name=company.get("display_name"),
        location_raw=location.get("display_name"),
        description_completeness=DescriptionCompleteness.EXCERPT,
        latitude=payload.get("latitude"),
        longitude=payload.get("longitude"),
        source_salary_predicted=parse_prediction_flag(
            payload.get("salary_is_predicted")
        ),
        source_salary_min=payload.get("salary_min"),
        source_salary_max=payload.get("salary_max"),
        contract_type_raw=_optional_text(payload.get("contract_type")),
        contract_time_raw=_optional_text(payload.get("contract_time")),
        source_category_raw=_optional_text(category.get("display_name")),
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


def parse_prediction_flag(value: str | None) -> bool | None:
    """Convert Adzuna's salary prediction flag to a nullable Boolean."""
    if value is None:
        return None
    if value == "1":
        return True
    if value == "0":
        return False

    raise ValueError(f"Invalid salary prediction flag: {value!r}")


def _optional_text(value: str | None) -> str | None:
    """Normalise empty optional text to None."""
    if value is None:
        return None

    value = value.strip()
    return value or None
