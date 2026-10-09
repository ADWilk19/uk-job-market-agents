from uk_job_market_agents.agents.workflow import (
    WorkflowResolution,
    ResolvedClassification,
)
from uk_job_market_agents.models.job_posting import (
    RoleFamily,
    WorkPattern,
)
from uk_job_market_agents.analytics.models import AnalyticalJobRecord
from uk_job_market_agents.analytics.salary_policy import annual_salary_bounds
from uk_job_market_agents.models.salary import SalaryQuote


def build_analytical_record(
    title: str,
    resolution: WorkflowResolution,
    salary: SalaryQuote | None,
) -> AnalyticalJobRecord | None:
    if resolution.requires_review or resolution.resolved is None:
        return None

    salary_min, salary_max = annual_salary_bounds(salary)

    return AnalyticalJobRecord(
        title=title,
        role_family=resolution.resolved.role_family,
        work_pattern=resolution.resolved.work_pattern,
        salary_min=salary_min,
        salary_max=salary_max,
    )


def test_builds_record_without_salary():
    resolution = WorkflowResolution(
        resolved=ResolvedClassification(
            role_family=RoleFamily.DATA_SCIENCE,
            work_pattern=WorkPattern.REMOTE,
        ),
        requires_review=False,
        review_reason=None,
    )

    record = build_analytical_record(
        title="Data Scientist",
        resolution=resolution,
        salary=None,
    )

    assert record is not None
    assert record.salary_min is None
    assert record.salary_max is None
    assert record.salary_midpoint is None


def test_does_not_build_record_without_resolution():
    resolution = WorkflowResolution(
        resolved=None,
        requires_review=False,
        review_reason=None,
    )

    record = build_analytical_record(
        title="Unclassified Data Role",
        resolution=resolution,
        salary=None,
    )

    assert record is None
