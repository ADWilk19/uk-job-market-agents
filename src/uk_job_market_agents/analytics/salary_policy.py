from uk_job_market_agents.models.salary import (
    SalaryPeriod,
    SalaryQuote,
)


def annual_salary_bounds(
    quote: SalaryQuote | None,
) -> tuple[int | None, int | None]:
    if quote is None:
        return None, None

    if quote.period != SalaryPeriod.YEAR:
        return None, None

    if quote.salary_min is None or quote.salary_max is None:
        return None, None

    return quote.salary_min, quote.salary_max
