import pytest
from pydantic import ValidationError

from datetime import datetime, timezone

from uk_job_market_agents.ingestion.adzuna import adapt_adzuna_job
from uk_job_market_agents.models.job_posting import DescriptionCompleteness


def test_adzuna_adapter_preserves_source_data():
    payload = {
        "id": "12345",
        "title": "Senior Data Engineer",
        "description": "Python, SQL and Airflow",
        "company": {"display_name": "Example Ltd"},
        "location": {"display_name": "London"},
        "redirect_url": "https://www.adzuna.co.uk/jobs/details/12345",
    }

    collected_at = datetime(
        2026, 10, 23, 8, 0, tzinfo=timezone.utc
    )

    job = adapt_adzuna_job(
        payload,
        collected_at=collected_at,
    )

    assert job.source == "adzuna"
    assert job.source_id == "12345"
    assert job.raw_title == payload["title"]
    assert job.raw_description == payload["description"]
    assert job.company_name == "Example Ltd"
    assert job.location_raw == "London"
    assert job.collected_at == collected_at
    assert str(job.source_url) == payload["redirect_url"]


def test_adzuna_adapter_rejects_null_source_id():
    payload = {
        "id": None,
        "title": "Senior Data Engineer",
        "description": "Python and SQL",
    }

    collected_at = datetime(
        2026, 10, 23, 8, 0, tzinfo=timezone.utc
    )

    with pytest.raises(ValidationError):
        adapt_adzuna_job(
            payload,
            collected_at=collected_at,
        )



@pytest.mark.parametrize(
    "field, invalid_value",
    [
        ("company", "Example Ltd"),
        ("location", ["London"]),
    ],
)
def test_adzuna_adapter_rejects_malformed_nested_fields(
    field,
    invalid_value,
):
    payload = {
        "id": "12345",
        "title": "Senior Data Engineer",
        "description": "Python and SQL",
        field: invalid_value,
    }

    collected_at = datetime(
        2026, 10, 23, 8, 0, tzinfo=timezone.utc
    )

    with pytest.raises(ValueError):
        adapt_adzuna_job(
            payload,
            collected_at=collected_at,
        )



def test_adzuna_adapter_accepts_missing_optional_metadata():
    payload = {
        "id": "12345",
        "title": "Data Engineer",
        "description": "Python and SQL",
    }

    collected_at = datetime(
        2026, 10, 23, 8, 0, tzinfo=timezone.utc
    )

    job = adapt_adzuna_job(
        payload,
        collected_at=collected_at,
    )

    assert job.company_name is None
    assert job.location_raw is None
    assert job.source_url is None



def test_adzuna_description_is_marked_as_excerpt():
    payload = {
        "id": "12345",
        "title": "Data Engineer",
        "description": "Python and SQL",
    }

    job = adapt_adzuna_job(
        payload,
        collected_at=datetime(
            2026, 10, 23, 8, 0, tzinfo=timezone.utc
        ),
    )

    assert job.description_completeness == DescriptionCompleteness.EXCERPT
