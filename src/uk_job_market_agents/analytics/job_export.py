
from pydantic import AwareDatetime, BaseModel

from uk_job_market_agents.agents.batch_orchestration import (
    BatchProcessingOutcome,
    ProcessingStatus,
)
from uk_job_market_agents.models.job_posting import (
    DescriptionCompleteness,
    JobPosting,
    RoleFamily,
    WorkPattern,
)
from uk_job_market_agents.agents.workflow import ReviewReason


class JobExportRow(BaseModel):
    """Represent one advertisement's analytical export row."""

    source: str
    source_id: str
    collected_at: AwareDatetime
    description_completeness: DescriptionCompleteness

    processing_status: ProcessingStatus

    company_name: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    source_salary_predicted: bool | None = None
    source_salary_min: float | None = None
    source_salary_max: float | None = None

    role_family: RoleFamily | None = None
    work_pattern: WorkPattern | None = None

    classification_review_reason: ReviewReason | None = None


def build_job_export_rows(
    postings: list[JobPosting],
    outcomes: list[BatchProcessingOutcome],
) -> list[JobExportRow]:
    """Pair ordered postings/outcomes; export analytics only for processed jobs."""

    rows = []

    for posting, outcome in zip(postings, outcomes, strict=True):
        if posting.source_id != outcome.job_id:
            raise ValueError("Posting and outcome identifiers do not match")

        analytical_record = (
            outcome.result.analytical_record
            if outcome.status == ProcessingStatus.PROCESSED and outcome.result is not None
            else None
        )

        row = JobExportRow(
            source=posting.source,
            source_id=posting.source_id,
            collected_at=posting.collected_at,
            description_completeness=posting.description_completeness,
            processing_status=outcome.status,
            source_salary_predicted=posting.source_salary_predicted,
            role_family=(
                analytical_record.role_family
                if analytical_record is not None
                else None
            ),
            work_pattern=(
                analytical_record.work_pattern
                if analytical_record is not None
                else None
            ),
            salary_min=(
                analytical_record.salary_min
                if analytical_record is not None
                else None
            ),
            salary_max=(
                analytical_record.salary_max
                if analytical_record is not None
                else None
            ),
            classification_review_reason=(
                outcome.result.classification.review_reason
                if outcome.result is not None
                else None
            ),
            source_salary_min=posting.source_salary_min,
            source_salary_max=posting.source_salary_max,
            company_name=posting.company_name,
        )

        rows.append(row)

    return rows
