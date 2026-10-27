from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from uk_job_market_agents.models.job_posting import (
    JobPosting,
    RoleFamily,
    Seniority,
    WorkPattern,
    DescriptionCompleteness,
)


def test_valid_job_posting():
    job = JobPosting(
        source_id="abc123",
        source="ad_example",
        collected_at=datetime.now(timezone.utc),
        raw_title="Senior Analytics Engineer",
        raw_description=(
            "Seeking an experienced analytics engineer "
            "with SQL, dbt and Python."
        ),
        location_raw="London",
        role_family=RoleFamily.ANALYTICS_ENGINEERING,
        seniority=Seniority.SENIOR,
        work_pattern=WorkPattern.HYBRID,
        salary_min=70000,
        salary_max=80000,
        skills=["SQL", "dbt", "Python"],
        classification_confidence=0.94,
    )

    assert job.role_family == RoleFamily.ANALYTICS_ENGINEERING
    assert job.salary_min == 70000
    assert "dbt" in job.skills


def test_negative_salary_is_rejected():
    with pytest.raises(ValidationError):
        JobPosting(
            source_id="abc123",
            source="ad_example",
            collected_at=datetime.now(timezone.utc),
            raw_title="Data Engineer",
            raw_description="Example",
            salary_min=-10000,
        )


def test_reversed_salary_range_is_rejected():
    with pytest.raises(ValidationError):
        JobPosting(
            source_id="abc123",
            source="ad_example",
            collected_at=datetime.now(timezone.utc),
            raw_title="Data Engineer",
            raw_description="Example",
            salary_min=80000,
            salary_max=70000,
        )


def test_confidence_above_one_is_rejected():
    with pytest.raises(ValidationError):
        JobPosting(
            source_id="abc123",
            source="ad_example",
            collected_at=datetime.now(timezone.utc),
            raw_title="Data Scientist",
            raw_description="Example",
            classification_confidence=1.5,
        )


@pytest.mark.parametrize(
    "source_id",
    ["", "   ", "\t"],
)
def test_empty_source_id_is_rejected(source_id):
    with pytest.raises(ValidationError):
        JobPosting(
            source_id=source_id,
            source="ad_example",
            collected_at=datetime.now(timezone.utc),
            raw_title="Data Engineer",
            raw_description="Example advertisement",
        )


@pytest.mark.parametrize(
    "source",
    ["", "   ", "\t"],
)
def test_empty_source_is_rejected(source):
    with pytest.raises(ValidationError):
        JobPosting(
            source_id="abc123",
            source=source,
            collected_at=datetime.now(timezone.utc),
            raw_title="Data Engineer",
            raw_description="Example advertisement",
        )


def test_naive_collection_timestamp_is_rejected():
    with pytest.raises(ValidationError):
        JobPosting(
            source_id="abc123",
            source="ad_example",
            collected_at=datetime(2026, 10, 22, 9, 0),
            raw_title="Data Engineer",
            raw_description="Example advertisement",
        )


def test_aware_collection_timestamp_is_accepted():
    collected_at = datetime(2026, 10, 22, 9, 0, tzinfo=timezone.utc)

    job = JobPosting(
        source_id="abc123",
        source="ad_example",
        collected_at=collected_at,
        raw_title="Data Engineer",
        raw_description="Example advertisement",
    )

    assert job.collected_at == collected_at
    assert job.collected_at.utcoffset() is not None


def test_job_posting_preserves_source_url():
    source_url = "https://www.example.com/jobs/abc123"

    job = JobPosting(
        source_id="abc123",
        source="ad_example",
        collected_at=datetime.now(timezone.utc),
        raw_title="Data Engineer",
        raw_description="Example advertisement",
        source_url=source_url,
    )

    assert str(job.source_url) == source_url


@pytest.mark.parametrize(
    "source_url",
    [
        "not-a-url",
        "ftp://example.com/jobs/123",
        "https://",
    ],
)
def test_invalid_source_url_is_rejected(source_url):
    with pytest.raises(ValidationError):
        JobPosting(
            source_id="abc123",
            source="ad_example",
            collected_at=datetime.now(timezone.utc),
            raw_title="Data Engineer",
            raw_description="Example advertisement",
            source_url=source_url,
        )


def test_source_url_is_optional():
    job = JobPosting(
        source_id="abc123",
        source="ad_example",
        collected_at=datetime.now(timezone.utc),
        raw_title="Data Engineer",
        raw_description="Example advertisement",
    )

    assert job.source_url is None


@pytest.mark.parametrize(
    "field",
    ["raw_title", "raw_description"],
)
@pytest.mark.parametrize(
    "value",
    ["", "   ", "\t"],
)
def test_blank_advertisement_content_is_rejected(field, value):
    data = {
        "source_id": "abc123",
        "source": "ad_example",
        "collected_at": datetime.now(timezone.utc),
        "raw_title": "Data Engineer",
        "raw_description": "Example advertisement",
    }

    data[field] = value

    with pytest.raises(ValidationError):
        JobPosting(**data)



def test_description_completeness_defaults_to_unknown():
    job = JobPosting(
        source_id="abc123",
        source="ad_example",
        collected_at=datetime.now(timezone.utc),
        raw_title="Data Engineer",
        raw_description="Python and SQL",
    )

    assert job.description_completeness == DescriptionCompleteness.UNKNOWN



def test_description_completeness_rejects_invalid_value():
    with pytest.raises(ValidationError) as exc_info:
        JobPosting(
            source_id="abc123",
            source="ad_example",
            collected_at=datetime.now(timezone.utc),
            raw_title="Data Engineer",
            raw_description="Python and SQL",
            description_completeness="probably_complete",
        )

    errors = exc_info.value.errors()

    assert len(errors) == 1
    assert errors[0]["loc"] == ("description_completeness",)
    assert errors[0]["type"] == "enum"


def test_job_posting_accepts_optional_coordinates():
    posting = JobPosting(
        **make_valid_job_data(),
        latitude=51.752281,
        longitude=-0.448284,
    )

    assert posting.latitude == 51.752281
    assert posting.longitude == -0.448284


@pytest.mark.parametrize(
    "latitude, longitude",
    [
        (91.0, 0.0),
        (-91.0, 0.0),
        (0.0, 181.0),
        (0.0, -181.0),
    ],
)
def test_job_posting_rejects_invalid_coordinates(
    latitude, longitude
):
    with pytest.raises(ValidationError):
        JobPosting(
            **make_valid_job_data(),
            latitude=latitude,
            longitude=longitude,
        )


def test_job_posting_rejects_incomplete_coordinate_pair():
    with pytest.raises(ValidationError):
        JobPosting(
            **make_valid_job_data(),
            latitude=51.752281,
        )


def make_valid_job_data():
    return {
        "source_id": "test-001",
        "source": "adzuna",
        "collected_at": datetime.now(timezone.utc),
        "raw_title": "Data Engineer",
        "raw_description": "Build and maintain data pipelines.",
    }
