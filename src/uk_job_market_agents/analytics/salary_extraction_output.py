"""Build auditable output rows from salary assessments."""

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from collections.abc import Iterable

from uk_job_market_agents.agents.salary_review import SalaryAssessment

@dataclass(frozen=True)
class SalaryExtractionRow:
    """A serializable record of a salary extraction assessment."""

    job_id: str
    salary_min: int | None
    salary_max: int | None
    period: str | None
    currency: str | None
    evidence: str | None
    review_status: str
    review_reason: str | None


def build_salary_extraction_row(
    job_id: str,
    assessment: SalaryAssessment,
) -> SalaryExtractionRow:
    """Convert a verified or reviewable salary assessment into an output row."""

    extraction = assessment.extraction
    salary = extraction.salary

    return SalaryExtractionRow(
        job_id=job_id,
        salary_min=salary.salary_min if salary is not None else None,
        salary_max=salary.salary_max if salary is not None else None,
        period=salary.period.value if salary is not None else None,
        currency=salary.currency if salary is not None else None,
        evidence=extraction.evidence,
        review_status=assessment.status.value,
        review_reason=assessment.reason,
    )


def write_salary_extraction_csv(
    rows: Iterable[SalaryExtractionRow],
    path: Path,
) -> None:
    """Write salary extraction rows to a CSV file."""

    fieldnames = [
        "job_id",
        "salary_min",
        "salary_max",
        "period",
        "currency",
        "evidence",
        "review_status",
        "review_reason",
    ]

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            lineterminator="\n"
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(asdict(row))
