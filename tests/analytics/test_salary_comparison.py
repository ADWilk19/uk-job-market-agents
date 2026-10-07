from uk_job_market_agents.analytics.comparison import (
    ComparisonStatus,
    compare_salary_summaries,
)
from uk_job_market_agents.analytics.summary import SalarySummary


def test_compare_salary_summaries_reports_difference():
    left = SalarySummary(
        records=2,
        records_with_salary=2,
        average_midpoint=65_000,
    )

    right = SalarySummary(
        records=2,
        records_with_salary=2,
        average_midpoint=60_000,
    )

    comparison = compare_salary_summaries(left, right)

    assert comparison.status == ComparisonStatus.OK
    assert comparison.difference == 5_000
    assert comparison.reason is None


def test_compare_salary_summaries_explains_insufficient_sample():
    left = SalarySummary(
        records=1,
        records_with_salary=1,
        average_midpoint=65_000,
    )

    right = SalarySummary(
        records=2,
        records_with_salary=2,
        average_midpoint=60_000,
    )

    comparison = compare_salary_summaries(left, right)

    assert comparison.status == ComparisonStatus.INSUFFICIENT_SAMPLE
    assert comparison.difference is None
    assert comparison.reason == (
        "Both groups require at least two salary-bearing records "
        "before a salary difference is reported."
    )
