import csv

from dataclasses import asdict

from uk_job_market_agents.agents.salary_extractor import (
    SalaryExtractionResult,
)
from uk_job_market_agents.agents.salary_review import (
    SalaryAssessment,
    SalaryReviewStatus,
)
from uk_job_market_agents.analytics.salary_extraction_output import (
    build_salary_extraction_row,
    write_salary_extraction_csv,
)


def test_builds_verified_salary_extraction_row():
    extraction = SalaryExtractionResult(
        salary={
            "salary_min": 65000,
            "salary_max": 80000,
            "period": "year",
            "currency": "GBP",
        },
        evidence="Salary: £65,000–£80,000 per annum.",
    )

    assessment = SalaryAssessment(
        extraction=extraction,
        status=SalaryReviewStatus.VERIFIED,
    )

    row = build_salary_extraction_row(
        job_id="advert-001",
        assessment=assessment,
    )

    assert asdict(row) == {
        "job_id": "advert-001",
        "salary_min": 65000,
        "salary_max": 80000,
        "period": "year",
        "currency": "GBP",
        "evidence": "Salary: £65,000–£80,000 per annum.",
        "review_status": "verified",
        "review_reason": None,
    }


def test_builds_row_when_salary_not_disclosed():
    extraction = SalaryExtractionResult(
        salary=None,
        evidence=None,
    )

    assessment = SalaryAssessment(
        extraction=extraction,
        status=SalaryReviewStatus.NOT_DISCLOSED,
    )

    row = build_salary_extraction_row(
        job_id="advert-002",
        assessment=assessment,
    )

    assert row.salary_min is None
    assert row.period is None
    assert row.evidence is None
    assert row.review_status == "not_disclosed"


def test_csv_export_preserves_missing_salary_values(tmp_path):
    extraction = SalaryExtractionResult(
        salary={
            "salary_min": 65000,
            "salary_max": None,
            "period": "year",
            "currency": "GBP",
        },
        evidence="£65,000 per annum",
    )

    assessment = SalaryAssessment(
        extraction=extraction,
        status=SalaryReviewStatus.REVIEW_REQUIRED,
        reason="Unsupported salary evidence format",
    )

    row = build_salary_extraction_row(
        job_id="advert-003",
        assessment=assessment,
    )

    output_path = tmp_path / "salary_extractions.csv"

    write_salary_extraction_csv(
        rows=[row],
        path=output_path,
    )

    with output_path.open(newline="", encoding="utf-8") as file:
        records = list(csv.DictReader(file))

    assert len(records) == 1
    assert records[0]["salary_min"] == "65000"
    assert records[0]["salary_max"] == ""
    assert records[0]["review_status"] == "review_required"


def test_csv_export_has_stable_header_and_lf_line_endings(tmp_path):
    output_path = tmp_path / "salary_extractions.csv"

    write_salary_extraction_csv(
        rows=[],
        path=output_path,
    )

    content = output_path.read_bytes()

    expected_header = (
        "job_id,salary_min,salary_max,period,currency,"
        "evidence,review_status,review_reason\n"
    )

    assert content == expected_header.encode("utf-8")


def test_csv_export_accepts_generator(tmp_path):
    """Export rows without requiring a list."""

    extraction = SalaryExtractionResult(
        salary={
            "salary_min": 65000,
            "salary_max": 80000,
            "period": "year",
            "currency": "GBP",
        },
        evidence="£65,000–£80,000 per annum",
    )

    assessment = SalaryAssessment(
        extraction=extraction,
        status=SalaryReviewStatus.VERIFIED,
    )

    def generate_rows():
        for job_id in ("advert-001", "advert-002"):
            yield build_salary_extraction_row(
                job_id=job_id,
                assessment=assessment,
            )

    output_path = tmp_path / "salary_extractions.csv"

    write_salary_extraction_csv(
        rows=generate_rows(),
        path=output_path,
    )

    with output_path.open(newline="", encoding="utf-8") as file:
        records = list(csv.DictReader(file))

    assert len(records) == 2
    assert [record["job_id"] for record in records] == ["advert-001", "advert-002"]


def test_csv_export_preserves_salary_evidence(tmp_path):
    evidence = "Salary: £65,000–£80,000 per annum."

    extraction = SalaryExtractionResult(
        salary={
            "salary_min": 65000,
            "salary_max": 80000,
            "period": "year",
            "currency": "GBP",
        },
        evidence=evidence,
    )

    assessment = SalaryAssessment(
        extraction=extraction,
        status=SalaryReviewStatus.VERIFIED,
    )

    row = build_salary_extraction_row(
        job_id="advert-004",
        assessment=assessment,
    )

    output_path = tmp_path / "salary_extractions.csv"

    write_salary_extraction_csv(
        rows=[row],
        path=output_path,
    )

    with output_path.open(newline="", encoding="utf-8") as file:
        records = list(csv.DictReader(file))

    assert records[0]["evidence"] == evidence


def test_csv_export_is_deterministic(tmp_path):
    extraction = SalaryExtractionResult(
        salary={
            "salary_min": 65000,
            "salary_max": 80000,
            "period": "year",
            "currency": "GBP",
        },
        evidence="£65,000–£80,000 per annum",
    )

    assessment = SalaryAssessment(
        extraction=extraction,
        status=SalaryReviewStatus.VERIFIED,
    )

    row = build_salary_extraction_row(
        job_id="advert-005",
        assessment=assessment,
    )

    first_path = tmp_path / "first.csv"
    second_path = tmp_path / "second.csv"

    write_salary_extraction_csv(
        rows=[row],
        path=first_path,
    )

    write_salary_extraction_csv(
        rows=[row],
        path=second_path,
    )

    first_bytes = first_path.read_bytes()
    second_bytes = second_path.read_bytes()

    assert first_bytes == second_bytes
