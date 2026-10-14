import pytest

from uk_job_market_agents.agents.salary_extractor import (
    SalaryExtractionResult,
)
from uk_job_market_agents.agents.salary_review import (
    SalaryAssessment,
    SalaryReviewStatus,
)
from uk_job_market_agents.analytics.salary_policy import (
    is_salary_eligible_for_analytics,
)


@pytest.mark.parametrize(
    "status,salary,expected",
    [
        (
            SalaryReviewStatus.VERIFIED,
            {
                "salary_min": 65000,
                "salary_max": 80000,
                "period": "year",
                "currency": "GBP",
            },
            True,
        ),
        (
            SalaryReviewStatus.REVIEW_REQUIRED,
            {
                "salary_min": 65000,
                "salary_max": 80000,
                "period": "year",
                "currency": "GBP",
            },
            False,
        ),
        (
            SalaryReviewStatus.VERIFIED,
            {
                "salary_min": 500,
                "salary_max": 650,
                "period": "day",
                "currency": "GBP",
            },
            False,
        ),
        (
            SalaryReviewStatus.NOT_DISCLOSED,
            None,
            False,
        ),
        (
            SalaryReviewStatus.VERIFIED,
            {
                "salary_min": 65000,
                "salary_max": None,
                "period": "year",
                "currency": "GBP",
            },
            False,
        ),
    ],
)
def test_salary_analytics_eligibility(status, salary, expected):
    extraction = SalaryExtractionResult(
        salary=salary,
        evidence=None,
    )

    assessment = SalaryAssessment(
        extraction=extraction,
        status=status,
    )

    result = is_salary_eligible_for_analytics(assessment)

    assert result == expected
