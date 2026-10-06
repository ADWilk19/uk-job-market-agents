from uk_job_market_agents.analytics.models import AnalyticalJobRecord
from uk_job_market_agents.analytics.summary import summarise_salaries
from uk_job_market_agents.models.job_posting import (
    RoleFamily,
    WorkPattern,
)


def test_summarise_salaries_calculates_average_midpoint():
    records = [
        AnalyticalJobRecord(
            title="Data Engineer",
            role_family=RoleFamily.DATA_ENGINEERING,
            work_pattern=WorkPattern.HYBRID,
            salary_min=50_000,
            salary_max=60_000,
        ),
        AnalyticalJobRecord(
            title="Senior Data Engineer",
            role_family=RoleFamily.DATA_ENGINEERING,
            work_pattern=WorkPattern.REMOTE,
            salary_min=60_000,
            salary_max=70_000,
        ),
    ]

    summary = summarise_salaries(records)

    assert summary.records == 2
    assert summary.records_with_salary == 2
    assert summary.average_midpoint == 60_000


def test_summarise_salaries_ignores_records_without_complete_salary():
    records = [
        AnalyticalJobRecord(
            title="Data Engineer",
            role_family=RoleFamily.DATA_ENGINEERING,
            work_pattern=WorkPattern.HYBRID,
            salary_min=50_000,
            salary_max=60_000,
        ),
        AnalyticalJobRecord(
            title="Senior Data Engineer",
            role_family=RoleFamily.DATA_ENGINEERING,
            work_pattern=WorkPattern.REMOTE,
        ),
    ]

    summary = summarise_salaries(records)

    assert summary.records == 2
    assert summary.records_with_salary == 1
    assert summary.average_midpoint == 55_000
