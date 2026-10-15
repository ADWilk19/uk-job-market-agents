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
    company_name: str | None = None,
    location_raw: str | None = None,
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
        company_name=company_name,
        location_raw=location_raw,
    )
