
import csv
import os
from contextlib import contextmanager
from pathlib import Path

import pytest
import uk_job_market_agents.analytics.analytical_report_csv as report_csv

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
    _serialize_samples_csv,
    _serialize_groups_csv,
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


def test_groups_directory_preflight_preserves_samples(tmp_path):
    report = build_analytical_report([])

    samples_path = tmp_path / "samples.csv"
    samples_path.write_bytes(b"original samples\n")

    groups_path = tmp_path / "groups"
    groups_path.mkdir()

    with pytest.raises(IsADirectoryError):
        write_analytical_report_csv(
            report, samples_path, groups_path
        )

    assert samples_path.read_bytes() == b"original samples\n"


@pytest.mark.parametrize("failure_at", ["samples.csv", "groups.csv"])
def test_replace_failure_is_propagated(tmp_path, monkeypatch, failure_at):
    report = build_analytical_report([])

    samples_path = tmp_path / "samples.csv"
    groups_path = tmp_path / "groups.csv"

    samples_path.write_bytes(b"original samples\n")
    groups_path.write_bytes(b"original groups\n")

    original_replace = os.replace

    def failing_replace(source, destination):
        if destination.name == failure_at:
            raise OSError("Simulated publication failure")
        return original_replace(source, destination)

    monkeypatch.setattr(os, "replace", failing_replace)

    with pytest.raises(
        OSError, match="Simulated publication failure"
    ):
        write_analytical_report_csv(
            report, samples_path, groups_path
        )

    if failure_at == "samples.csv":
        assert samples_path.read_bytes() == b"original samples\n"
    else:
        assert samples_path.read_bytes() == (
            b"total,role_eligible,role_eligible_rate,"
            b"salary_eligible,salary_eligible_rate\n0,0,,0,\n"
        )

    # The second replacement failed.
    assert groups_path.read_bytes() == b"original groups\n"

    # Neither staging file remains.
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "groups.csv",
        "samples.csv",
    ]


def test_serialization_does_not_modify_report():
    report = build_analytical_report([])
    before = report.model_dump()

    _serialize_samples_csv(report)
    _serialize_groups_csv(report)

    assert report.model_dump() == before


def test_staging_failure_preserves_existing_outputs(
    tmp_path, monkeypatch
):
    report = build_analytical_report([])

    samples_path = tmp_path / "samples.csv"
    groups_path = tmp_path / "groups.csv"

    samples_path.write_bytes(b"original samples\n")
    groups_path.write_bytes(b"original groups\n")

    original_temporary_file = report_csv.tempfile.NamedTemporaryFile
    staged_count = 0

    @contextmanager
    def failing_temporary_file(**kwargs):
        nonlocal staged_count
        staged_count += 1
        with original_temporary_file(**kwargs) as staged_file:
            if staged_count == 2:
                original_write = staged_file.write

                def failing_write(content):
                    original_write(content[:8])
                    raise OSError("Simulated staging failure")

                monkeypatch.setattr(staged_file, "write", failing_write)
            yield staged_file

    monkeypatch.setattr(
        report_csv.tempfile, "NamedTemporaryFile", failing_temporary_file
    )

    with pytest.raises(
        OSError, match="Simulated staging failure"
    ):
        write_analytical_report_csv(
            report, samples_path, groups_path
        )

    assert samples_path.read_bytes() == b"original samples\n"
    assert groups_path.read_bytes() == b"original groups\n"

    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "groups.csv",
        "samples.csv",
    ]


def test_publication_preserves_symlink_and_replaces_target(tmp_path):
    report = build_analytical_report([])
    target = tmp_path / "existing.csv"
    target.write_bytes(b"original samples\n")
    link = tmp_path / "samples.csv"
    link.symlink_to(target.name)

    with target.open("rb") as original:
        write_analytical_report_csv(report, link, tmp_path / "groups.csv")
        assert original.read() == b"original samples\n"

    assert link.is_symlink()
    assert target.read_bytes().endswith(b"0,0,,0,\n")


def test_existing_hardlink_alias_is_rejected(tmp_path):
    report = build_analytical_report([])
    samples = tmp_path / "samples.csv"
    groups = tmp_path / "groups.csv"
    samples.write_bytes(b"original samples\n")
    os.link(samples, groups)

    with pytest.raises(ValueError, match="Report output paths must be distinct"):
        write_analytical_report_csv(report, samples, groups)

    assert samples.samefile(groups)
    assert samples.read_bytes() == b"original samples\n"


@pytest.mark.parametrize("parent_is_file", [False, True])
def test_invalid_parent_preserves_existing_output(tmp_path, parent_is_file):
    report = build_analytical_report([])
    samples = tmp_path / "samples.csv"
    samples.write_bytes(b"original samples\n")
    parent = tmp_path / "parent"
    if parent_is_file:
        parent.touch()

    with pytest.raises(NotADirectoryError):
        write_analytical_report_csv(report, samples, parent / "groups.csv")

    assert samples.read_bytes() == b"original samples\n"


def test_cleanup_failure_preserves_original_error_and_attempts_both_unlinks(
    tmp_path, monkeypatch
):
    report = build_analytical_report([])
    original_unlink = Path.unlink
    cleanup_attempts = []

    def failing_replace(source, destination):
        raise OSError("Simulated publication failure")

    def failing_first_unlink(path, *args, **kwargs):
        cleanup_attempts.append(path)
        if len(cleanup_attempts) == 1:
            raise PermissionError("Simulated cleanup failure")
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(os, "replace", failing_replace)
    monkeypatch.setattr(Path, "unlink", failing_first_unlink)

    with pytest.raises(OSError, match="Simulated publication failure"):
        write_analytical_report_csv(
            report, tmp_path / "samples.csv", tmp_path / "groups.csv"
        )

    assert len(cleanup_attempts) == 2
    assert list(tmp_path.iterdir()) == cleanup_attempts[:1]
