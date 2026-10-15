import pytest
from pydantic import ValidationError

from uk_job_market_agents.analytics.models import AnalyticalJobRecord
from uk_job_market_agents.models.job_posting import (
    RoleFamily,
    WorkPattern,
)


def test_analytical_job_record_accepts_salary_range():
    record = AnalyticalJobRecord(
        title="Data Engineer",
        role_family=RoleFamily.DATA_ENGINEERING,
        work_pattern=WorkPattern.HYBRID,
        salary_min=55_000,
        salary_max=65_000,
    )

    assert record.salary_min == 55_000
    assert record.salary_max == 65_000


def test_analytical_job_record_allows_missing_salary():
    record = AnalyticalJobRecord(
        title="Senior Data Engineer",
        role_family=RoleFamily.DATA_ENGINEERING,
        work_pattern=WorkPattern.REMOTE,
    )

    assert record.salary_min is None
    assert record.salary_max is None


def test_analytical_job_record_rejects_inverted_salary_range():
    with pytest.raises(ValidationError):
        AnalyticalJobRecord(
            title="Data Engineer",
            role_family=RoleFamily.DATA_ENGINEERING,
            work_pattern=WorkPattern.HYBRID,
            salary_min=70_000,
            salary_max=60_000,
        )


def test_salary_midpoint_is_calculated():
    record = AnalyticalJobRecord(
        title="Data Engineer",
        role_family=RoleFamily.DATA_ENGINEERING,
        work_pattern=WorkPattern.HYBRID,
        salary_min=55_000,
        salary_max=65_000,
    )

    assert record.salary_midpoint == 60_000


def test_salary_midpoint_is_none_when_salary_is_incomplete():
    record = AnalyticalJobRecord(
        title="Data Engineer",
        role_family=RoleFamily.DATA_ENGINEERING,
        work_pattern=WorkPattern.REMOTE,
        salary_min=55_000,
    )

    assert record.salary_midpoint is None


def test_analytical_record_preserves_company_and_location():
    record = AnalyticalJobRecord(
        title="Senior Data Engineer",
        company_name="Example Analytics Ltd",
        location_raw="Southampton, Hampshire",
        role_family=RoleFamily.DATA_ENGINEERING,
        work_pattern=WorkPattern.HYBRID,
        salary_min=60000,
        salary_max=80000,
    )

    assert record.company_name == "Example Analytics Ltd"
    assert record.location_raw == "Southampton, Hampshire"
    assert record.salary_midpoint == 70000


def test_analytical_record_accepts_missing_company_and_location():
    record = AnalyticalJobRecord(
        title="Data Scientist",
        role_family=RoleFamily.DATA_SCIENCE,
        work_pattern=WorkPattern.REMOTE,
    )

    assert record.company_name is None
    assert record.location_raw is None
