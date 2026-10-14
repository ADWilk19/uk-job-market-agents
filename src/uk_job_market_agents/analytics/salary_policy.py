from uk_job_market_agents.agents.salary_review import (
    SalaryAssessment,
    SalaryReviewStatus,
)
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


def is_salary_eligible_for_analytics(
    assessment: SalaryAssessment,
) -> bool:
    """Determine whether an extracted salary can enter annual analytics."""

    if assessment.status != SalaryReviewStatus.VERIFIED:
        return False

    salary = assessment.extraction.salary

    lower, upper = annual_salary_bounds(salary)

    if lower is None or upper is None:
        return False

    return True
