from dataclasses import dataclass

from uk_job_market_agents.analytics.models import AnalyticalJobRecord
from uk_job_market_agents.analytics.summary import (
    summarise_salaries,
    summarise_salaries_by_role_family,
    summarise_salaries_by_work_pattern,
)


@dataclass(frozen=True)
class SalaryAnalysisRow:
    dimension: str
    segment: str
    records: int
    records_with_salary: int
    average_midpoint: float | None
    has_sufficient_sample: bool


def build_salary_analysis_rows(
    records: list[AnalyticalJobRecord],
) -> list[SalaryAnalysisRow]:
    rows = []

    overall = summarise_salaries(records)

    rows.append(
        SalaryAnalysisRow(
            dimension="overall",
            segment="all",
            records=overall.records,
            records_with_salary=overall.records_with_salary,
            average_midpoint=overall.average_midpoint,
            has_sufficient_sample=overall.has_sufficient_sample,
        )
    )

    for summary in summarise_salaries_by_role_family(records):
        rows.append(
            SalaryAnalysisRow(
                dimension="role_family",
                segment=summary.role_family.value,
                records=summary.records,
                records_with_salary=summary.records_with_salary,
                average_midpoint=summary.average_midpoint,
                has_sufficient_sample=summary.records_with_salary >= 2,
            )
        )

    for summary in summarise_salaries_by_work_pattern(records):
        rows.append(
            SalaryAnalysisRow(
                dimension="work_pattern",
                segment=summary.work_pattern.value,
                records=summary.records,
                records_with_salary=summary.records_with_salary,
                average_midpoint=summary.average_midpoint,
                has_sufficient_sample=summary.records_with_salary >= 2,
            )
        )

    return rows
