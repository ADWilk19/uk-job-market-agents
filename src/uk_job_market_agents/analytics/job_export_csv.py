
import csv
from pathlib import Path

from uk_job_market_agents.analytics.job_export import JobExportRow


JOB_EXPORT_COLUMNS = [
    "source",
    "source_id",
    "collected_at",
    "description_completeness",
    "processing_status",
    "role_family",
    "work_pattern",
    "salary_min",
    "salary_max",
    "source_salary_min",
    "source_salary_max",
    "source_salary_predicted",
    "classification_review_reason",
    "company_name",
]


def write_job_export_csv(
    rows: list[JobExportRow],
    output_path: Path,
) -> None:
    """Write ordered rows as UTF-8 CSV with a fixed header and LF terminators."""

    with output_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=JOB_EXPORT_COLUMNS,
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            values = row.model_dump(mode="json")

            writer.writerow({
                column: values[column]
                for column in JOB_EXPORT_COLUMNS
            })
