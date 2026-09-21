from datetime import datetime

import pytest
from pydantic import ValidationError

from uk_job_market_agents.models.job_posting import (
    JobPosting,
    RoleFamily,
    Seniority,
    WorkPattern,
)


def test_valid_job_posting():
    job = JobPosting(
        source_id="abc123",
        source="ad_example",
        collected_at=datetime.now(),
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
            collected_at=datetime.now(),
            raw_title="Data Engineer",
            raw_description="Example",
            salary_min=-10000,
        )


def test_reversed_salary_range_is_rejected():
    with pytest.raises(ValidationError):
        JobPosting(
            source_id="abc123",
            source="ad_example",
            collected_at=datetime.now(),
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
            collected_at=datetime.now(),
            raw_title="Data Scientist",
            raw_description="Example",
            classification_confidence=1.5,
        )
