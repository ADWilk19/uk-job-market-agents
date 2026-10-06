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
