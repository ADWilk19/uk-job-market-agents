from pydantic import BaseModel

from uk_job_market_agents.agents.salary_review import SalaryAssessment
from uk_job_market_agents.agents.salary_workflow import run_salary_workflow
from uk_job_market_agents.agents.workflow import (
    WorkflowResolution,
    run_classification_workflow,
    resolve_classification,
)
from uk_job_market_agents.analytics.models import AnalyticalJobRecord
from uk_job_market_agents.analytics.record_builder import (
    build_analytical_record,
)
from uk_job_market_agents.analytics.salary_integration import (
    apply_salary_assessment,
)
from uk_job_market_agents.models.job_posting import JobPosting


class OrchestrationResult(BaseModel):
    """Represent the outcome of processing a job advertisement."""

    classification: WorkflowResolution
    analytical_record: AnalyticalJobRecord | None = None
    salary_assessment: SalaryAssessment | None = None


def process_job(job: JobPosting) -> OrchestrationResult:
    """Coordinate classification, salary verification and record construction."""

    workflow = run_classification_workflow(
        title=job.raw_title,
        description=job.raw_description,
    )

    resolution = resolve_classification(workflow)

    record = build_analytical_record(
        title=job.raw_title,
        resolution=resolution,
        salary=None,
        company_name=job.company_name,
        location_raw=job.location_raw,
    )

    if record is None:
        return OrchestrationResult(
            classification=resolution,
        )

    assessment = run_salary_workflow(job.raw_description)

    record = apply_salary_assessment(
        record=record,
        assessment=assessment,
    )

    return OrchestrationResult(
        classification=resolution,
        analytical_record=record,
        salary_assessment=assessment,
    )
