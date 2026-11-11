
import csv

import pytest

from tests.analytics.test_grouped_summary import make_row
from uk_job_market_agents.agents.batch_orchestration import ProcessingStatus
from uk_job_market_agents.analytics.analytical_dataset import (
    AnalyticalSampleSummary,
)
from uk_job_market_agents.analytics.analytical_report import (
    AnalyticalReport,
    build_analytical_report,
)
from uk_job_market_agents.analytics.analytical_report_csv import (
    write_analytical_report_csv,
)
from uk_job_market_agents.analytics.data_quality import (
    CoverageMetric,
)
from uk_job_market_agents.analytics.grouped_summary import (
    RoleFamilySummary,
)
from uk_job_market_agents.models.job_posting import RoleFamily


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def test_empty_report_writes_headers_and_undefined_rates(tmp_path):
    report = build_analytical_report([])
    samples_path = tmp_path / "samples.csv"
    groups_path = tmp_path / "groups.csv"

    write_analytical_report_csv(
        report,
        samples_path,
        groups_path,
    )

    assert read_csv(samples_path) == [
        {
            "total": "0",
            "role_eligible": "0",
            "role_eligible_rate": "",
            "salary_eligible": "0",
            "salary_eligible_rate": "",
        }
    ]

    assert read_csv(groups_path) == []

    assert samples_path.read_bytes() == (
        b"total,role_eligible,role_eligible_rate,"
        b"salary_eligible,salary_eligible_rate\n"
        b"0,0,,0,\n"
    )
    assert groups_path.read_bytes() == (
        b"role_family,role_count,verified_salary_count,verified_salary_rate\n"
    )


def test_empty_report_export_is_deterministic(tmp_path):
    report = build_analytical_report([])
    samples_path = tmp_path / "samples.csv"
    groups_path = tmp_path / "groups.csv"

    write_analytical_report_csv(
        report, samples_path, groups_path
    )

    original_samples = samples_path.read_bytes()
    original_groups = groups_path.read_bytes()

    write_analytical_report_csv(
        report, samples_path, groups_path
    )

    assert samples_path.read_bytes() == original_samples
    assert groups_path.read_bytes() == original_groups


def test_populated_report_exports_reconciled_counts(tmp_path):
    rows = [
        make_row(
            source_id="job-1",
            processing_status=ProcessingStatus.PROCESSED,
            role_family=RoleFamily.DATA_SCIENCE,
            salary_min=50000,
            salary_max=65000,
        ),
        make_row(
            source_id="job-2",
            processing_status=ProcessingStatus.PROCESSED,
            role_family=RoleFamily.DATA_ENGINEERING,
            salary_min=60000,
            salary_max=75000,
        ),
        make_row(
            source_id="job-3",
            processing_status=ProcessingStatus.PROCESSED,
            role_family=RoleFamily.DATA_ENGINEERING,
        ),
        make_row(
            source_id="job-4",
            processing_status=ProcessingStatus.PROCESSED,
            role_family=None,
            salary_min=45000,
            salary_max=55000,
        ),
        make_row(
            source_id="job-5",
            processing_status=ProcessingStatus.REVIEW_REQUIRED,
            role_family=None,
        ),
    ]

    built_report = build_analytical_report(rows)
    report = AnalyticalReport(
        samples=built_report.samples,
        groups=list(reversed(built_report.groups)),
    )
    before = report.model_dump()

    samples_path = tmp_path / "samples.csv"
    groups_path = tmp_path / "groups.csv"

    write_analytical_report_csv(
        report, samples_path, groups_path
    )

    assert samples_path.read_bytes() == (
        b"total,role_eligible,role_eligible_rate,"
        b"salary_eligible,salary_eligible_rate\n"
        b"5,3,0.6,3,0.6\n"
    )
    assert groups_path.read_bytes() == (
        b"role_family,role_count,verified_salary_count,verified_salary_rate\n"
        b"data_engineering,2,1,0.5\n"
        b"data_science,1,1,1.0\n"
    )

    assert report.model_dump() == before


def test_export_rejects_colliding_output_paths(tmp_path):
    report = build_analytical_report([])
    output_path = tmp_path / "report.csv"

    with pytest.raises(
        ValueError,
        match="Report output paths must be distinct",
    ):
        write_analytical_report_csv(
            report,
            output_path,
            output_path,
        )

    assert not output_path.exists()


@pytest.mark.parametrize("use_symlink", [False, True])
def test_colliding_paths_preserve_existing_output(tmp_path, use_symlink):
    report = build_analytical_report([])
    output_path = tmp_path / "existing.csv"
    output_path.write_text(
        "existing content\n",
        encoding="utf-8",
    )

    groups_path = output_path
    if use_symlink:
        groups_path = tmp_path / "alias.csv"
        groups_path.symlink_to(output_path.name)

    with pytest.raises(
        ValueError,
        match="Report output paths must be distinct",
    ):
        write_analytical_report_csv(
            report,
            output_path,
            groups_path,
        )

    assert output_path.read_text(encoding="utf-8") == (
        "existing content\n"
    )


def test_zero_count_group_has_undefined_salary_rate(tmp_path):
    samples = AnalyticalSampleSummary(
        total=0,
        role_eligible=CoverageMetric(
            populated=0, total=0, rate=None
        ),
        salary_eligible=CoverageMetric(
            populated=0, total=0, rate=None
        ),
    )

    report = AnalyticalReport(
        samples=samples,
        groups=[
            RoleFamilySummary(
                role_family=RoleFamily.DATA_ENGINEERING,
                role_count=0,
                verified_salary_count=0,
            )
        ],
    )

    samples_path = tmp_path / "samples.csv"
    groups_path = tmp_path / "groups.csv"

    write_analytical_report_csv(
        report, samples_path, groups_path
    )

    assert read_csv(groups_path) == [
        {
            "role_family": "data_engineering",
            "role_count": "0",
            "verified_salary_count": "0",
            "verified_salary_rate": "",
        }
    ]
