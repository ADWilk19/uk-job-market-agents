
"""Deterministic coverage metrics for exported job advertisements."""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel, Field, model_validator

from uk_job_market_agents.analytics.job_export import JobExportRow
from uk_job_market_agents.models.job_posting import (
    DescriptionCompleteness,
    WorkPattern,
)


class CoverageMetric(BaseModel):
    """Store an auditable numerator, denominator and coverage rate."""

    populated: int = Field(ge=0)
    total: int = Field(ge=0)
    rate: float | None = Field(default=None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_consistency(self) -> CoverageMetric:
        """Enforce valid counts and a consistent coverage rate."""
        if self.populated > self.total:
            raise ValueError("Populated count cannot exceed total")

        if self.total == 0:
            if self.rate is not None:
                raise ValueError("Rate must be None when total is zero")
        else:
            expected = self.populated / self.total

            if self.rate is None or abs(self.rate - expected) > 1e-9:
                raise ValueError("Rate must equal populated / total")

        return self


class DataQualitySummary(BaseModel):
    """Summarise coverage without interpreting advertisement content."""

    total: int = Field(ge=0)
    company_coverage: CoverageMetric
    approved_role_coverage: CoverageMetric
    known_work_pattern_coverage: CoverageMetric
    provider_salary_coverage: CoverageMetric
    verified_salary_coverage: CoverageMetric
    complete_description_coverage: CoverageMetric

    @model_validator(mode="after")
    def validate_denominators(self) -> DataQualitySummary:
        """Require every coverage denominator to match the summary total."""
        for field_name in type(self).model_fields:
            if field_name == "total":
                continue

            metric = getattr(self, field_name)

            if metric.total != self.total:
                raise ValueError(
                    "Coverage denominator must match summary total"
                )

        return self


def _coverage(populated: int, total: int) -> CoverageMetric:
    """Calculate coverage, preserving undefined empty-sample rates."""
    return CoverageMetric(
        populated=populated,
        total=total,
        rate=populated / total if total else None,
    )


def summarize_data_quality(
    rows: Sequence[JobExportRow],
) -> DataQualitySummary:
    """Calculate deterministic quality metrics from exported job rows."""
    total = len(rows)

    return DataQualitySummary(
        total=total,
        company_coverage=_coverage(
            sum(
                bool(row.company_name and row.company_name.strip())
                for row in rows
            ),
            total,
        ),
        approved_role_coverage=_coverage(
            sum(row.role_family is not None for row in rows),
            total,
        ),
        known_work_pattern_coverage=_coverage(
            sum(
                row.work_pattern in {
                    WorkPattern.REMOTE,
                    WorkPattern.HYBRID,
                    WorkPattern.ONSITE,
                }
                for row in rows
            ),
            total,
        ),
        provider_salary_coverage=_coverage(
            sum(
                row.source_salary_min is not None
                and row.source_salary_max is not None
                for row in rows
            ),
            total,
        ),
        verified_salary_coverage=_coverage(
            sum(
                row.salary_min is not None
                and row.salary_max is not None
                for row in rows
            ),
            total,
        ),
        complete_description_coverage=_coverage(
            sum(
                row.description_completeness
                == DescriptionCompleteness.COMPLETE
                for row in rows
            ),
            total,
        ),
    )
