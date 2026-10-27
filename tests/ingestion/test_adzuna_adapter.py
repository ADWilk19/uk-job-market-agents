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


def test_adzuna_adapter_preserves_coordinates():
    payload = {
        "id": "12345",
        "title": "Data Engineer",
        "description": "Python and SQL",
        "latitude": 51.752281,
        "longitude": -0.448284,
    }

    job = adapt_adzuna_job(
        payload,
        collected_at=datetime(
            2026, 10, 23, 8, 0, tzinfo=timezone.utc
        ),
    )

    assert job.latitude == 51.752281
    assert job.longitude == -0.448284


def test_adzuna_adapter_accepts_missing_coordinates():
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

    assert job.latitude is None
    assert job.longitude is None


@pytest.mark.parametrize(
    "prediction_flag, expected",
    [
        ("1", True),
        ("0", False),
        (None, None),
    ],
)
def test_adzuna_adapter_parses_salary_prediction(
    prediction_flag,
    expected,
):
    payload = {
        "id": "12345",
        "title": "Data Engineer",
        "description": "Python and SQL",
    }

    if prediction_flag is not None:
        payload["salary_is_predicted"] = prediction_flag

    job = adapt_adzuna_job(
        payload,
        collected_at=datetime(
            2026, 10, 23, 8, 0, tzinfo=timezone.utc
        ),
    )

    assert job.source_salary_predicted is expected


def test_adzuna_adapter_rejects_invalid_salary_prediction():
    payload = {
        "id": "12345",
        "title": "Data Engineer",
        "description": "Python and SQL",
        "salary_is_predicted": "unknown",
    }

    with pytest.raises(ValueError):
        adapt_adzuna_job(
            payload,
            collected_at=datetime(
                2026, 10, 23, 8, 0, tzinfo=timezone.utc
            ),
        )


def test_adzuna_adapter_preserves_valid_source_salaries():
    payload = {
        "salary_min":40000,
        "salary_max":50000,
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

    assert job.source_salary_min == 40000
    assert job.source_salary_max == 50000
    assert job.salary_min is None
    assert job.salary_max is None


def test_adzuna_adapter_rejects_an_inverted_source_range():
    payload = {
        "id": "12345",
        "title": "Data Engineer",
        "description": "Python and SQL",
        "salary_min": 60000,
        "salary_max": 40000,
    }

    with pytest.raises(ValueError, match="Salary minimum cannot exceed maximum"):
        adapt_adzuna_job(
            payload,
            collected_at=datetime(
                2026, 10, 23, 8, 0, tzinfo=timezone.utc
            ),
        )


def test_adzuna_adapter_preserves_published_at():
    payload = {
            "salary_min":40000,
            "salary_max":50000,
            "id": "12345",
            "title": "Data Engineer",
            "description": "Python and SQL",
            "created": "2026-10-23T08:30:00Z"
        }

    job = adapt_adzuna_job(
        payload,
        collected_at=datetime(
            2026, 10, 23, 8, 0, tzinfo=timezone.utc
        ),
    )

    assert job.published_at == datetime(
    2026, 10, 23, 8, 30, tzinfo=timezone.utc
)

    assert job.published_at.tzinfo is not None

    assert job.collected_at == datetime(
        2026, 10, 23, 8, 0, tzinfo=timezone.utc
    )


def test_adzuna_adapter_preserves_populated_contract_metadata():
    payload = {
        "salary_min":40000,
        "salary_max":50000,
        "id": "12345",
        "title": "Data Engineer",
        "description": "Python and SQL",
        "created": "2026-10-23T08:30:00Z",
        "contract_type": "permanent",
        "contract_time": "full_time",
        "category": {
            "display_name": "IT Jobs",
        }
    }

    job = adapt_adzuna_job(
        payload,
        collected_at=datetime(
            2026, 10, 23, 8, 0, tzinfo=timezone.utc
        ),
    )

    assert job.contract_type_raw == "permanent"
    assert job.contract_time_raw == "full_time"
    assert job.source_category_raw == "IT Jobs"


def test_adzuna_adapter_accepts_null_contract_metadata():
    payload = {
        "salary_min":40000,
        "salary_max":50000,
        "id": "12345",
        "title": "Data Engineer",
        "description": "Python and SQL",
        "created": "2026-10-23T08:30:00Z",
        "contract_type": None,
        "contract_time": None,
        "category": {
            "display_name": None,
        }
    }

    job = adapt_adzuna_job(
        payload,
        collected_at=datetime(
            2026, 10, 23, 8, 0, tzinfo=timezone.utc
        ),
    )

    assert job.contract_type_raw is None
    assert job.contract_time_raw is None
    assert job.source_category_raw is None

def test_adzuna_adapter_normalises_empty_contract_metadata():
    payload = {
        "salary_min":40000,
        "salary_max":50000,
        "id": "12345",
        "title": "Data Engineer",
        "description": "Python and SQL",
        "created": "2026-10-23T08:30:00Z",
        "contract_type": "",
        "contract_time": "",
        "category": {
            "display_name": "",
        }
    }

    job = adapt_adzuna_job(
        payload,
        collected_at=datetime(
            2026, 10, 23, 8, 0, tzinfo=timezone.utc
        ),
    )

    assert job.contract_type_raw is None
    assert job.contract_time_raw is None
    assert job.source_category_raw is None


def test_adzuna_adapter_rejects_naive_publication_timestamp():
    payload = {
        "id": "12345",
        "title": "Data Engineer",
        "description": "Python and SQL",
        "created": "2026-10-23T08:30:00",
    }

    with pytest.raises(
        ValueError,
        match="timezone",
    ):
        adapt_adzuna_job(
            payload,
            collected_at=datetime(
                2026, 10, 23, 9, 0, tzinfo=timezone.utc
            ),
        )
