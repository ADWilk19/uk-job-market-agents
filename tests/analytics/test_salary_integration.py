from uk_job_market_agents.agents.salary_extractor import (
    SalaryExtractionResult,
)
from uk_job_market_agents.agents.salary_review import (
    SalaryAssessment,
    SalaryReviewStatus,
)
from uk_job_market_agents.analytics.models import AnalyticalJobRecord
from uk_job_market_agents.analytics.salary_integration import (
    apply_salary_assessment,
)
from uk_job_market_agents.models.job_posting import (
    RoleFamily,
    WorkPattern,
)
from uk_job_market_agents.analytics.summary import summarise_salaries


def test_verified_annual_salary_enters_analytical_record():
    record = AnalyticalJobRecord(
        title="Senior Data Engineer",
        role_family=RoleFamily.DATA_ENGINEERING,
        work_pattern=WorkPattern.REMOTE,
    )

    assessment = SalaryAssessment(
        extraction=SalaryExtractionResult(
            salary={
                "salary_min": 60000,
                "salary_max": 80000,
                "period": "year",
                "currency": "GBP",
            },
            evidence="£60,000–£80,000 per annum",
        ),
        status=SalaryReviewStatus.VERIFIED,
    )

    updated = apply_salary_assessment(record, assessment)

    assert updated.salary_min == 60000
    assert updated.salary_max == 80000
    assert updated.salary_midpoint == 70000.0

    assert updated.title == record.title
    assert updated.role_family == record.role_family
    assert updated.work_pattern == record.work_pattern

    assert record.salary_min is None
    assert record.salary_max is None


def test_review_required_salary_clears_existing_bounds():
    record = AnalyticalJobRecord(
        title="Senior Data Engineer",
        role_family=RoleFamily.DATA_ENGINEERING,
        work_pattern=WorkPattern.REMOTE,
        salary_min=90000,
        salary_max=110000,
    )

    assessment = SalaryAssessment(
        extraction=SalaryExtractionResult(
            salary={
                "salary_min": 70000,
                "salary_max": 90000,
                "period": "year",
                "currency": "GBP",
            },
            evidence="£70,000–£90,000 per annum",
        ),
        status=SalaryReviewStatus.REVIEW_REQUIRED,
    )

    updated = apply_salary_assessment(record, assessment)

    assert updated.salary_min is None
    assert updated.salary_max is None
    assert updated.salary_midpoint is None

    # The original record must remain unchanged.
    assert record.salary_min == 90000
    assert record.salary_max == 110000


def test_verified_daily_salary_is_excluded():
    record = AnalyticalJobRecord(
        title="Contract Data Engineer",
        role_family=RoleFamily.DATA_ENGINEERING,
        work_pattern=WorkPattern.REMOTE,
    )

    assessment = SalaryAssessment(
        extraction=SalaryExtractionResult(
            salary={
                "salary_min": 500,
                "salary_max": 600,
                "period": "day",
                "currency": "GBP",
            },
            evidence="£500–£600 per day",
        ),
        status=SalaryReviewStatus.VERIFIED,
    )

    updated = apply_salary_assessment(record, assessment)

    assert updated.salary_min is None
    assert updated.salary_max is None
    assert updated.salary_midpoint is None


def test_salary_analytics_excludes_ineligible_assessments():
    records = [
        apply_salary_assessment(
            AnalyticalJobRecord(
                title="Senior Data Engineer",
                role_family=RoleFamily.DATA_ENGINEERING,
                work_pattern=WorkPattern.REMOTE,
            ),
            SalaryAssessment(
                extraction=SalaryExtractionResult(
                    salary={
                        "salary_min": 60000,
                        "salary_max": 80000,
                        "period": "year",
                        "currency": "GBP",
                    },
                    evidence="£60,000–£80,000 per annum",
                ),
                status=SalaryReviewStatus.VERIFIED,
            ),
        ),
        apply_salary_assessment(
            AnalyticalJobRecord(
                title="Contract Data Engineer",
                role_family=RoleFamily.DATA_ENGINEERING,
                work_pattern=WorkPattern.REMOTE,
            ),
            SalaryAssessment(
                extraction=SalaryExtractionResult(
                    salary={
                        "salary_min": 500,
                        "salary_max": 600,
                        "period": "day",
                        "currency": "GBP",
                    },
                    evidence="£500–£600 per day",
                ),
                status=SalaryReviewStatus.VERIFIED,
            ),
        ),
        apply_salary_assessment(
            AnalyticalJobRecord(
                title="Senior Data Engineer",
                role_family=RoleFamily.DATA_ENGINEERING,
                work_pattern=WorkPattern.REMOTE,
            ),
            SalaryAssessment(
                extraction=SalaryExtractionResult(
                    salary={
                        "salary_min": 70000,
                        "salary_max": 90000,
                        "period": "year",
                        "currency": "GBP",
                    },
                    evidence="£70,000–£90,000 per annum",
                ),
                status=SalaryReviewStatus.REVIEW_REQUIRED,
            ),
        ),
    ]

    summary = summarise_salaries(records)

    assert summary.records == 3
    assert summary.records_with_salary == 1
    assert summary.average_midpoint == 70000.0
