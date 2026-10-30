
import csv

import pytest

from datetime import datetime, timezone

from uk_job_market_agents.analytics.job_export import JobExportRow
from uk_job_market_agents.analytics.job_export_csv import (
    write_job_export_csv,
)
from uk_job_market_agents.agents.batch_orchestration import ProcessingStatus
from uk_job_market_agents.models.job_posting import (
    DescriptionCompleteness,
    RoleFamily,
    WorkPattern,
)


def test_empty_job_export_writes_header(tmp_path):
    output_path = tmp_path / "job_export.csv"

    write_job_export_csv([], output_path)

    with output_path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        reader = csv.reader(file)
        rows = list(reader)

    assert rows == [
        [
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
            "company_name"
        ]
    ]


def test_job_export_writes_one_row(tmp_path):
    output_path = tmp_path / "job_export.csv"

    row = JobExportRow(
        source="adzuna",
        source_id="job-001",
        collected_at=datetime(
            2026, 10, 29, 12, 30, tzinfo=timezone.utc
        ),
        description_completeness=DescriptionCompleteness.EXCERPT,
        processing_status=ProcessingStatus.PROCESSED,
        role_family=RoleFamily.DATA_ENGINEERING,
        work_pattern=WorkPattern.HYBRID,
        salary_min=45000,
        salary_max=55000,
        source_salary_min=40000.0,
        source_salary_max=60000.0,
        source_salary_predicted=True,
    )

    write_job_export_csv([row], output_path)

    with output_path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        records = list(csv.DictReader(file))

    assert len(records) == 1

    record = records[0]

    assert record["source"] == "adzuna"
    assert record["source_id"] == "job-001"
    assert record["collected_at"] == "2026-10-29T12:30:00Z"
    assert record["description_completeness"] == "excerpt"
    assert record["processing_status"] == "processed"
    assert record["role_family"] == RoleFamily.DATA_ENGINEERING.value
    assert record["work_pattern"] == WorkPattern.HYBRID.value
    assert record["salary_min"] == "45000"
    assert record["salary_max"] == "55000"
    assert record["source_salary_min"] == "40000.0"
    assert record["source_salary_max"] == "60000.0"
    assert record["source_salary_predicted"] == "True"
    assert record["classification_review_reason"] == ""


def test_job_export_is_deterministic(tmp_path):
    rows = [
        JobExportRow(
            source="adzuna",
            source_id="job-001",
            collected_at=datetime(
                2026, 10, 29, 12, 30, tzinfo=timezone.utc
            ),
            description_completeness=DescriptionCompleteness.EXCERPT,
            processing_status=ProcessingStatus.PROCESSED,
            role_family=RoleFamily.DATA_ENGINEERING,
            work_pattern=WorkPattern.HYBRID,
            salary_min=45000,
            salary_max=55000,
            source_salary_min=40000.0,
            source_salary_max=60000.0,
            source_salary_predicted=True,
        ),
        JobExportRow(
            source="adzuna",
            source_id="job-002",
            collected_at=datetime(
                2026, 10, 29, 12, 30, tzinfo=timezone.utc
            ),
            description_completeness=DescriptionCompleteness.EXCERPT,
            processing_status=ProcessingStatus.FAILED,
            source_salary_min=40000.0,
            source_salary_max=60000.0,
            source_salary_predicted=True,
        )
    ]
    first_path = tmp_path / "first.csv"
    second_path = tmp_path / "second.csv"

    write_job_export_csv(rows, first_path)
    write_job_export_csv(rows, second_path)

    with first_path.open(
    "r",
    encoding="utf-8",
    newline="",
    ) as file:
        records = list(csv.DictReader(file))

    assert len(records) == 2

    assert [record["source_id"] for record in records] == [
        "job-001",
        "job-002",
    ]

    assert records[1]["processing_status"] == "failed"
    assert records[1]["salary_min"] == ""
    assert records[1]["salary_max"] == ""

    assert first_path.read_bytes() == second_path.read_bytes()



def test_job_export_escapes_special_characters(tmp_path):
    output_path = tmp_path / "special_characters.csv"

    company_name = 'Smith, Jones & "Partners"\nUK Division'

    row = JobExportRow(
        source="adzuna",
        source_id="job-005",
        collected_at=datetime(
            2026, 10, 29, 12, 30, tzinfo=timezone.utc
        ),
        description_completeness=DescriptionCompleteness.EXCERPT,
        processing_status=ProcessingStatus.PROCESSED,
        company_name=company_name,
    )

    write_job_export_csv([row], output_path)

    with output_path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        records = list(csv.DictReader(file))

    assert len(records) == 1
    assert records[0]["company_name"] == company_name
    assert records[0]["source_id"] == "job-005"


@pytest.mark.parametrize("predicted, expected", [(True, "True"), (False, "False"), (None, "")])
def test_job_export_prediction_flag_and_lf_bytes(tmp_path, predicted, expected):
    row = JobExportRow(
        source="fixture",
        source_id="001",
        collected_at=datetime(2026, 10, 29, tzinfo=timezone.utc),
        description_completeness=DescriptionCompleteness.UNKNOWN,
        processing_status=ProcessingStatus.FAILED,
        source_salary_predicted=predicted,
        company_name="Café",
    )
    path = tmp_path / "flags.csv"
    write_job_export_csv([row], path)
    data = path.read_bytes()
    assert b"\r" not in data
    assert data.endswith(b"\n")
    record = next(csv.DictReader(data.decode("utf-8").splitlines()))
    assert record["source_salary_predicted"] == expected
    assert record["company_name"] == "Café"
