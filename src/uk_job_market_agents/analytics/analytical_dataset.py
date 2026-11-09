
"""Deterministic selection of analysis-eligible job advertisements."""

from collections.abc import Sequence
from pydantic import BaseModel, Field, model_validator

from uk_job_market_agents.agents.batch_orchestration import ProcessingStatus
from uk_job_market_agents.analytics.data_quality import CoverageMetric
from uk_job_market_agents.analytics.job_export import JobExportRow


def select_role_eligible_rows(
    rows: Sequence[JobExportRow],
) -> list[JobExportRow]:
    """Select processed advertisements with approved role classifications."""
    return [
        row
        for row in rows
        if (
            row.processing_status == ProcessingStatus.PROCESSED
            and row.role_family is not None
        )
    ]


def select_salary_eligible_rows(
    rows: Sequence[JobExportRow],
) -> list[JobExportRow]:
    """Select processed jobs with complete verified analytical salary bounds."""
    return [
        row
        for row in rows
        if (
            row.processing_status == ProcessingStatus.PROCESSED
            and row.salary_min is not None
            and row.salary_max is not None
        )
    ]



class AnalyticalSampleSummary(BaseModel):
    """Record analytical eligibility against the full input population."""

    total: int = Field(ge=0)
    role_eligible: CoverageMetric
    salary_eligible: CoverageMetric

    @model_validator(mode="after")
    def validate_denominators(self) -> "AnalyticalSampleSummary":
        """Require eligibility denominators to match the population."""
        if (
            self.role_eligible.total != self.total
            or self.salary_eligible.total != self.total
        ):
            raise ValueError(
                "Eligibility denominator must match summary total"
            )

        return self


def summarize_analytical_samples(
    rows: Sequence[JobExportRow],
) -> AnalyticalSampleSummary:
    """Summarise eligible observations without modifying input rows."""
    total = len(rows)

    role_count = len(select_role_eligible_rows(rows))
    salary_count = len(select_salary_eligible_rows(rows))

    return AnalyticalSampleSummary(
        total=total,
        role_eligible=CoverageMetric(
            populated=role_count,
            total=total,
            rate=role_count / total if total else None,
        ),
        salary_eligible=CoverageMetric(
            populated=salary_count,
            total=total,
            rate=salary_count / total if total else None,
        ),
    )
