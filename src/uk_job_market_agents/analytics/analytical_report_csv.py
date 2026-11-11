
"""Deterministic CSV serialization for validated analytical reports."""

import csv
from pathlib import Path

from uk_job_market_agents.analytics.analytical_report import (
    AnalyticalReport,
)


SAMPLE_COLUMNS = [
    "total",
    "role_eligible",
    "role_eligible_rate",
    "salary_eligible",
    "salary_eligible_rate",
]

GROUP_COLUMNS = [
    "role_family",
    "role_count",
    "verified_salary_count",
    "verified_salary_rate",
]


def write_analytical_report_csv(
    report: AnalyticalReport,
    samples_path: Path,
    groups_path: Path,
) -> None:
    """Write analytical samples and role-family summaries as CSV files."""

    if samples_path.resolve() == groups_path.resolve():
        raise ValueError(
            "Report output paths must be distinct"
        )

    with samples_path.open(
        "w", encoding="utf-8", newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=SAMPLE_COLUMNS,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerow(
            {
                "total": report.samples.total,
                "role_eligible": report.samples.role_eligible.populated,
                "role_eligible_rate": (
                    report.samples.role_eligible.rate
                    if report.samples.role_eligible.rate is not None
                    else ""
                ),
                "salary_eligible": report.samples.salary_eligible.populated,
                "salary_eligible_rate": (
                    report.samples.salary_eligible.rate
                    if report.samples.salary_eligible.rate is not None
                    else ""
                ),
            }
        )

    with groups_path.open(
        "w", encoding="utf-8", newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=GROUP_COLUMNS,
            lineterminator="\n",
        )
        writer.writeheader()

        for group in sorted(
            report.groups,
            key=lambda item: item.role_family.value,
        ):
            writer.writerow(
                {
                    "role_family": group.role_family.value,
                    "role_count": group.role_count,
                    "verified_salary_count": group.verified_salary_count,
                    "verified_salary_rate": (
                        group.verified_salary_count / group.role_count
                        if group.role_count > 0
                        else ""
                    ),
                }
            )
