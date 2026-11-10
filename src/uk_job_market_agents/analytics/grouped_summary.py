
"""Deterministic role-family summaries for analytical job exports."""

from collections import Counter
from collections.abc import Sequence

from pydantic import BaseModel, Field, model_validator

from uk_job_market_agents.analytics.analytical_dataset import (
    select_role_eligible_rows,
    select_salary_eligible_rows,
)
from uk_job_market_agents.analytics.job_export import JobExportRow
from uk_job_market_agents.models.job_posting import RoleFamily


class RoleFamilySummary(BaseModel):
    """Record approved role counts and verified salary coverage."""

    role_family: RoleFamily
    role_count: int = Field(ge=0)
    verified_salary_count: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_counts(self) -> "RoleFamilySummary":
        """Verified salary observations cannot exceed role observations."""
        if self.verified_salary_count > self.role_count:
            raise ValueError(
                "Verified salary count cannot exceed role count"
            )
        return self


def summarize_by_role_family(
    rows: Sequence[JobExportRow],
) -> list[RoleFamilySummary]:
    """Group approved roles and their verified salary observations."""
    role_rows = select_role_eligible_rows(rows)
    salary_rows = select_salary_eligible_rows(role_rows)

    role_counts = Counter(
        row.role_family for row in role_rows
    )
    salary_counts = Counter(
        row.role_family for row in salary_rows
    )

    return [
        RoleFamilySummary(
            role_family=role_family,
            role_count=role_counts[role_family],
            verified_salary_count=salary_counts[role_family],
        )
        for role_family in sorted(role_counts, key=lambda role: role.value)
    ]
