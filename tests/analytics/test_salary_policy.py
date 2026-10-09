import pytest

from uk_job_market_agents.analytics.salary_policy import (
    annual_salary_bounds,
)
from uk_job_market_agents.models.salary import SalaryQuote


@pytest.mark.parametrize(
    "salary_min,salary_max,period,expected",
    [
        (55_000, 65_000, "year", (55_000, 65_000)),
        (None, 70_000, "year", (None, None)),
        (45_000, None, "year", (None, None)),
        (450, 550, "day", (None, None)),
        (25, 35, "hour", (None, None)),
    ],
)
def test_annual_salary_bounds(
    salary_min,
    salary_max,
    period,
    expected,
):
    quote = SalaryQuote(
        salary_min=salary_min,
        salary_max=salary_max,
        period=period,
    )

    assert annual_salary_bounds(quote) == expected


def test_missing_salary_is_not_eligible():
    assert annual_salary_bounds(None) == (None, None)
