import pytest
from pydantic import ValidationError

from uk_job_market_agents.models.salary import (
    SalaryPeriod,
    SalaryQuote,
)


def test_annual_salary_range():
    quote = SalaryQuote(
        salary_min=55_000,
        salary_max=65_000,
        period="year",
    )

    assert quote.period is SalaryPeriod.YEAR
    assert quote.currency == "GBP"


def test_upper_bound_only():
    quote = SalaryQuote(
        salary_max=70_000,
        period=SalaryPeriod.YEAR,
    )

    assert quote.salary_min is None


@pytest.mark.parametrize(
    "bounds",
    [
        {"salary_min": 70_000, "salary_max": 60_000},
        {"salary_min": -1, "salary_max": 60_000},
        {"salary_min": None, "salary_max": None},
        {"salary_min": 55_000.5, "salary_max": 65_000},
    ],
)
def test_invalid_bounds(bounds):
    with pytest.raises(ValidationError):
        SalaryQuote(**bounds, period="year")


def test_day_rate_is_not_annual():
    quote = SalaryQuote(
        salary_min=450,
        salary_max=550,
        period="day",
    )

    assert quote.period is SalaryPeriod.DAY


def test_non_gbp_currency_is_rejected():
    with pytest.raises(ValidationError):
        SalaryQuote(
            salary_min=60_000,
            period="year",
            currency="USD",
        )


@pytest.mark.parametrize(
    "salary_min,salary_max,period,expected",
    [
        (55_000, 65_000, "year", True),
        (None, 70_000, "year", False),
        (45_000, None, "year", False),
        (450, 550, "day", False),
        (25, 35, "hour", False),
    ],
)
def test_salary_analytics_eligibility(
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

    assert quote.is_annual_salary_range is expected
