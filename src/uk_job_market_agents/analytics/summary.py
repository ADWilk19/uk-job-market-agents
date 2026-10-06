from dataclasses import dataclass
from statistics import mean

from uk_job_market_agents.analytics.models import AnalyticalJobRecord
from uk_job_market_agents.models.job_posting import RoleFamily


@dataclass(frozen=True)
class SalarySummary:
    records: int
    records_with_salary: int
    average_midpoint: float | None


@dataclass(frozen=True)
class RoleFamilySalarySummary:
    role_family: RoleFamily
    records: int
    records_with_salary: int
    average_midpoint: float | None


def summarise_salaries(
    records: list[AnalyticalJobRecord],
) -> SalarySummary:
    midpoints = [
        record.salary_midpoint
        for record in records
        if record.salary_midpoint is not None
    ]

    return SalarySummary(
        records=len(records),
        records_with_salary=len(midpoints),
        average_midpoint=mean(midpoints) if midpoints else None,
    )


def summarise_salaries_by_role_family(
    records: list[AnalyticalJobRecord],
) -> list[RoleFamilySalarySummary]:
    summaries = []

    for role_family in RoleFamily:
        matching_records = [
            record
            for record in records
            if record.role_family == role_family
        ]

        if not matching_records:
            continue

        salary_summary = summarise_salaries(matching_records)

        summaries.append(
            RoleFamilySalarySummary(
                role_family=role_family,
                records=salary_summary.records,
                records_with_salary=salary_summary.records_with_salary,
                average_midpoint=salary_summary.average_midpoint,
            )
        )

    return summaries
