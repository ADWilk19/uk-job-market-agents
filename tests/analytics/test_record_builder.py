from uk_job_market_agents.agents.workflow import (
    ResolvedClassification,
    WorkflowResolution,
    ReviewReason,
)
from uk_job_market_agents.analytics.record_builder import (
    build_analytical_record,
)
from uk_job_market_agents.models.job_posting import (
    RoleFamily,
    WorkPattern,
)
from uk_job_market_agents.models.salary import SalaryQuote


def test_builds_record_with_eligible_annual_salary():
    resolution = WorkflowResolution(
        resolved=ResolvedClassification(
            role_family=RoleFamily.DATA_ENGINEERING,
            work_pattern=WorkPattern.REMOTE,
        ),
        requires_review=False,
        review_reason=None,
    )

    salary = SalaryQuote(
        salary_min=60_000,
        salary_max=80_000,
        period="year",
    )

    record = build_analytical_record(
        title="Senior Data Engineer",
        resolution=resolution,
        salary=salary,
    )

    assert record is not None
    assert record.title == "Senior Data Engineer"
    assert record.role_family == RoleFamily.DATA_ENGINEERING
    assert record.work_pattern == WorkPattern.REMOTE
    assert record.salary_min == 60_000
    assert record.salary_max == 80_000
    assert record.salary_midpoint == 70_000


def test_excludes_salary_that_is_not_annual():
    resolution = WorkflowResolution(
        resolved=ResolvedClassification(
            role_family=RoleFamily.DATA_ENGINEERING,
            work_pattern=WorkPattern.HYBRID,
        ),
        requires_review=False,
        review_reason=None,
    )

    salary = SalaryQuote(
        salary_min=450,
        salary_max=550,
        period="day",
    )

    record = build_analytical_record(
        title="Contract Data Engineer",
        resolution=resolution,
        salary=salary,
    )

    assert record is not None
    assert record.salary_min is None
    assert record.salary_max is None
    assert record.salary_midpoint is None


def test_does_not_build_record_when_review_is_required():
    resolution = WorkflowResolution(
        resolved=None,
        requires_review=True,
        review_reason=ReviewReason.ROLE_FAMILY,
    )

    record = build_analytical_record(
        title="Ambiguous Data Role",
        resolution=resolution,
        salary=None,
    )

    assert record is None
