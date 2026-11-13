"""Validate analytical reports through a downstream CSV reader."""

import csv

from tests.analytics.test_grouped_summary import make_row
from uk_job_market_agents.agents.batch_orchestration import ProcessingStatus
from uk_job_market_agents.analytics.analytical_report import (
    build_analytical_report,
)
from uk_job_market_agents.analytics.analytical_report_csv import (
    write_analytical_report_csv,
)
from uk_job_market_agents.models.job_posting import RoleFamily


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def test_offline_report_reconciles_after_csv_round_trip(tmp_path):
    rows = [
        make_row(
            "de-verified",
            role_family=RoleFamily.DATA_ENGINEERING,
            salary_min=45000,
            salary_max=55000,
        ),
        make_row(
            "de-provider-only",
            role_family=RoleFamily.DATA_ENGINEERING,
            source_salary_min=50000,
            source_salary_max=60000,
        ),
        make_row(
            "ds-verified",
            role_family=RoleFamily.DATA_SCIENCE,
            salary_min=60000,
            salary_max=70000,
        ),
        # Supply analytical fields on ineligible statuses to exercise the
        # selectors' status checks independently of the upstream row builder.
        make_row(
            "review",
            processing_status=ProcessingStatus.REVIEW_REQUIRED,
            role_family=RoleFamily.DATA_ENGINEERING,
            salary_min=50000,
            salary_max=60000,
        ),
        make_row(
            "failed",
            processing_status=ProcessingStatus.FAILED,
            role_family=RoleFamily.DATA_SCIENCE,
            salary_min=60000,
            salary_max=70000,
        ),
    ]

    report = build_analytical_report(rows)
    samples_path = tmp_path / "samples.csv"
    groups_path = tmp_path / "groups.csv"

    write_analytical_report_csv(
        report, samples_path, groups_path
    )

    samples = read_csv(samples_path)
    groups = read_csv(groups_path)

    assert samples == [{
        "total": "5",
        "role_eligible": "3",
        "role_eligible_rate": "0.6",
        "salary_eligible": "2",
        "salary_eligible_rate": "0.4",
    }]

    assert groups == [
        {
            "role_family": "data_engineering",
            "role_count": "2",
            "verified_salary_count": "1",
            "verified_salary_rate": "0.5",
        },
        {
            "role_family": "data_science",
            "role_count": "1",
            "verified_salary_count": "1",
            "verified_salary_rate": "1.0",
        },
    ]

    assert sum(int(g["role_count"]) for g in groups) == int(
        samples[0]["role_eligible"]
    )
    assert sum(
        int(g["verified_salary_count"]) for g in groups
    ) == int(samples[0]["salary_eligible"])


def test_unclassified_verified_salary_remains_outside_groups(tmp_path):
    rows = [
        make_row(
            "classified",
            role_family=RoleFamily.DATA_ENGINEERING,
            salary_min=50000,
            salary_max=60000,
        ),
        make_row(
            "unclassified",
            role_family=None,
            salary_min=45000,
            salary_max=55000,
        ),
        make_row(
            "review",
            processing_status=ProcessingStatus.REVIEW_REQUIRED,
        ),
    ]

    report = build_analytical_report(rows)
    samples_path = tmp_path / "samples.csv"
    groups_path = tmp_path / "groups.csv"

    write_analytical_report_csv(
        report, samples_path, groups_path
    )

    [sample] = read_csv(samples_path)
    groups = read_csv(groups_path)

    assert sample["total"] == "3"
    assert sample["role_eligible"] == "1"
    assert sample["salary_eligible"] == "2"
    assert float(sample["role_eligible_rate"]) == 1 / 3
    assert float(sample["salary_eligible_rate"]) == 2 / 3

    assert groups == [
        {
            "role_family": "data_engineering",
            "role_count": "1",
            "verified_salary_count": "1",
            "verified_salary_rate": "1.0",
        }
    ]

    ungrouped_salary_count = (
        int(sample["salary_eligible"])
        - sum(int(group["verified_salary_count"]) for group in groups)
    )
    assert ungrouped_salary_count == 1


def test_empty_report_is_readable_by_downstream_consumer(tmp_path):
    report = build_analytical_report([])

    samples_path = tmp_path / "samples.csv"
    groups_path = tmp_path / "groups.csv"

    write_analytical_report_csv(
        report, samples_path, groups_path
    )

    samples = read_csv(samples_path)
    groups = read_csv(groups_path)

    assert samples == [{
        "total": "0",
        "role_eligible": "0",
        "role_eligible_rate": "",
        "salary_eligible": "0",
        "salary_eligible_rate": "",
    }]

    assert groups == []
