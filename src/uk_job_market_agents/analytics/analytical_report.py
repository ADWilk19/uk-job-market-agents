from collections.abc import Sequence

from pydantic import BaseModel, model_validator

from uk_job_market_agents.analytics.analytical_dataset import (
    AnalyticalSampleSummary,
    summarize_analytical_samples,
)
from uk_job_market_agents.analytics.grouped_summary import (
    RoleFamilySummary,
    summarize_by_role_family,
)
from uk_job_market_agents.analytics.job_export import JobExportRow


class AnalyticalReport(BaseModel):
    samples: AnalyticalSampleSummary
    groups: list[RoleFamilySummary]

    @model_validator(mode="after")
    def validate_reconciliation(self) -> "AnalyticalReport":
        if len({group.role_family for group in self.groups}) != len(self.groups):
            raise ValueError("Role family groups must be unique")

        role_count = self.samples.role_eligible.populated
        if sum(group.role_count for group in self.groups) != role_count:
            raise ValueError(
                "Grouped roles must reconcile with role eligibility"
            )

        grouped_salary_count = sum(
            group.verified_salary_count
            for group in self.groups
        )

        salary_count = self.samples.salary_eligible.populated
        if grouped_salary_count > salary_count:
            raise ValueError(
                "Grouped verified salaries exceed salary eligibility"
            )

        outside_role_sample = self.samples.total - role_count
        if salary_count - grouped_salary_count > outside_role_sample:
            raise ValueError(
                "Ungrouped verified salaries exceed rows outside role eligibility"
            )

        return self


def build_analytical_report(
    rows: Sequence[JobExportRow],
) -> AnalyticalReport:
    return AnalyticalReport(
        samples=summarize_analytical_samples(rows),
        groups=summarize_by_role_family(rows),
    )
