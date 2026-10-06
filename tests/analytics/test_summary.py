from uk_job_market_agents.analytics.models import AnalyticalJobRecord
from uk_job_market_agents.analytics.summary import (
    summarise_salaries,
    summarise_salaries_by_role_family,
    summarise_salaries_by_work_pattern,
    )
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


def test_summarise_salaries_by_role_family():
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
        AnalyticalJobRecord(
            title="Data Scientist",
            role_family=RoleFamily.DATA_SCIENCE,
            work_pattern=WorkPattern.HYBRID,
            salary_min=55_000,
            salary_max=65_000,
        ),
    ]

    summaries = summarise_salaries_by_role_family(records)

    engineering = next(
        summary
        for summary in summaries
        if summary.role_family == RoleFamily.DATA_ENGINEERING
    )

    data_science = next(
        summary
        for summary in summaries
        if summary.role_family == RoleFamily.DATA_SCIENCE
    )

    assert engineering.records == 2
    assert engineering.average_midpoint == 60_000

    assert data_science.records == 1
    assert data_science.average_midpoint == 60_000


def test_summarise_salaries_by_work_pattern():
    records = [
        AnalyticalJobRecord(
            title="Data Engineer",
            role_family=RoleFamily.DATA_ENGINEERING,
            work_pattern=WorkPattern.REMOTE,
            salary_min=50_000,
            salary_max=60_000,
        ),
        AnalyticalJobRecord(
            title="Data Scientist",
            role_family=RoleFamily.DATA_SCIENCE,
            work_pattern=WorkPattern.REMOTE,
            salary_min=60_000,
            salary_max=70_000,
        ),
        AnalyticalJobRecord(
            title="Analytics Engineer",
            role_family=RoleFamily.ANALYTICS_ENGINEERING,
            work_pattern=WorkPattern.HYBRID,
            salary_min=45_000,
            salary_max=55_000,
        ),
    ]

    summaries = summarise_salaries_by_work_pattern(records)

    remote = next(
        summary
        for summary in summaries
        if summary.work_pattern == WorkPattern.REMOTE
    )

    hybrid = next(
        summary
        for summary in summaries
        if summary.work_pattern == WorkPattern.HYBRID
    )

    assert remote.records == 2
    assert remote.records_with_salary == 2
    assert remote.average_midpoint == 60_000

    assert hybrid.records == 1
    assert hybrid.records_with_salary == 1
    assert hybrid.average_midpoint == 50_000


def test_salary_summary_has_sufficient_sample_with_two_salary_records():
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
    ]

    summary = summarise_salaries(records)

    assert summary.has_sufficient_sample is True


def test_salary_summary_has_insufficient_sample_with_one_salary_record():
    records = [
        AnalyticalJobRecord(
            title="Data Engineer",
            role_family=RoleFamily.DATA_ENGINEERING,
            work_pattern=WorkPattern.REMOTE,
            salary_min=50_000,
            salary_max=60_000,
        )
    ]

    summary = summarise_salaries(records)

    assert summary.has_sufficient_sample is False
