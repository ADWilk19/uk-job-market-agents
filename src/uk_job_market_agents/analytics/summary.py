from dataclasses import dataclass
from statistics import mean

from uk_job_market_agents.analytics.models import AnalyticalJobRecord


@dataclass(frozen=True)
class SalarySummary:
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
