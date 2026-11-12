
"""Deterministic CSV serialization for validated analytical reports."""

import csv
import io
import os
import tempfile
from contextlib import suppress
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


def _serialize_samples_csv(report: AnalyticalReport) -> str:
    output = io.StringIO(newline="")

    writer = csv.DictWriter(
        output,
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

    return output.getvalue()


def _serialize_groups_csv(report: AnalyticalReport) -> str:
    output = io.StringIO(newline="")

    writer = csv.DictWriter(
        output,
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

    return output.getvalue()


def _stage_csv(content: str, destination: Path) -> Path:
    """Stage CSV content in the destination directory."""
    staged_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=destination.parent,
            prefix=".report-",
            suffix=".tmp",
            delete=False,
        ) as file:
            staged_path = Path(file.name)
            file.write(content)

        return staged_path

    except BaseException:
        if staged_path is not None:
            with suppress(OSError):
                staged_path.unlink(missing_ok=True)
        raise


def write_analytical_report_csv(
    report: AnalyticalReport,
    samples_path: Path,
    groups_path: Path,
) -> None:
    """Write analytical samples and role-family summaries as CSV files."""

    for destination in (samples_path, groups_path):
        if not destination.parent.is_dir():
            raise NotADirectoryError(destination.parent)

    # Publish to the same targets that the previous direct writer opened.
    samples_path = samples_path.resolve()
    groups_path = groups_path.resolve()

    if samples_path == groups_path or (
        samples_path.exists()
        and groups_path.exists()
        and samples_path.samefile(groups_path)
    ):
        raise ValueError("Report output paths must be distinct")

    for destination in (samples_path, groups_path):
        if not destination.parent.is_dir():
            raise NotADirectoryError(destination.parent)
        if destination.is_dir():
            raise IsADirectoryError(destination)
        if destination.exists() and not destination.is_file():
            raise ValueError(f"Report output must be a regular file: {destination}")

    staged_samples = None
    staged_groups = None

    samples_csv = _serialize_samples_csv(report)
    groups_csv = _serialize_groups_csv(report)

    try:
        staged_samples = _stage_csv(samples_csv, samples_path)
        staged_groups = _stage_csv(groups_csv, groups_path)

        os.replace(staged_samples, samples_path)
        staged_samples = None
        os.replace(staged_groups, groups_path)

    except BaseException:
        for staged_path in (staged_samples, staged_groups):
            if staged_path is not None:
                with suppress(OSError):
                    staged_path.unlink(missing_ok=True)
        raise
