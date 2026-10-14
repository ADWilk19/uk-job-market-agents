from uk_job_market_agents.agents.salary_review import SalaryAssessment
from uk_job_market_agents.analytics.models import AnalyticalJobRecord
from uk_job_market_agents.analytics.salary_policy import (
    annual_salary_bounds,
    is_salary_eligible_for_analytics,
)


def apply_salary_assessment(
    record: AnalyticalJobRecord,
    assessment: SalaryAssessment,
) -> AnalyticalJobRecord:
    """Return an analytical record containing only eligible salary bounds."""

    if not is_salary_eligible_for_analytics(assessment):
        return record.model_copy(
            update={
                "salary_min": None,
                "salary_max": None,
            }
        )

    lower, upper = annual_salary_bounds(
        assessment.extraction.salary
    )

    return record.model_copy(
        update={
            "salary_min": lower,
            "salary_max": upper,
        }
    )
