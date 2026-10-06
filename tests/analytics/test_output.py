from uk_job_market_agents.analytics.models import AnalyticalJobRecord
from uk_job_market_agents.analytics.output import build_salary_analysis_rows
from uk_job_market_agents.models.job_posting import (
    RoleFamily,
    WorkPattern,
)


def test_build_salary_analysis_rows():
    records = [
        AnalyticalJobRecord(
            title="Data Engineer",
            role_family=RoleFamily.DATA_ENGINEERING,
            work_pattern=WorkPattern.REMOTE,
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
        AnalyticalJobRecord(
            title="Data Scientist",
            role_family=RoleFamily.DATA_SCIENCE,
            work_pattern=WorkPattern.HYBRID,
            salary_min=55_000,
            salary_max=65_000,
        ),
    ]

    rows = build_salary_analysis_rows(records)

    overall = next(
        row
        for row in rows
        if row.dimension == "overall"
    )

    engineering = next(
        row
        for row in rows
        if (
            row.dimension == "role_family"
            and row.segment == RoleFamily.DATA_ENGINEERING.value
        )
    )

    hybrid = next(
        row
        for row in rows
        if (
            row.dimension == "work_pattern"
            and row.segment == WorkPattern.HYBRID.value
        )
    )

    assert overall.records == 3
    assert overall.average_midpoint == 60_000
    assert overall.has_sufficient_sample is True

    assert engineering.records == 2
    assert engineering.average_midpoint == 60_000
    assert engineering.has_sufficient_sample is True

    assert hybrid.records == 1
    assert hybrid.average_midpoint == 60_000
    assert hybrid.has_sufficient_sample is False
