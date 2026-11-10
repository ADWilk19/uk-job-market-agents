import pytest
from pydantic import ValidationError

from tests.analytics.test_grouped_summary import make_row
from uk_job_market_agents.agents.batch_orchestration import ProcessingStatus
from uk_job_market_agents.analytics.analytical_dataset import AnalyticalSampleSummary
from uk_job_market_agents.analytics.analytical_report import (
    AnalyticalReport,
    build_analytical_report,
)
from uk_job_market_agents.analytics.data_quality import CoverageMetric
from uk_job_market_agents.analytics.grouped_summary import RoleFamilySummary
from uk_job_market_agents.models.job_posting import RoleFamily


rows = [
    make_row(
        source_id="job-1",
        processing_status=ProcessingStatus.PROCESSED,
        role_family=RoleFamily.DATA_ENGINEERING,
    ),
    make_row(
        source_id="job-2",
        processing_status=ProcessingStatus.REVIEW_REQUIRED,
        role_family=None,
    ),
    make_row(
        source_id="job-3",
        processing_status=ProcessingStatus.FAILED,
        role_family=None,
    ),
]


def test_empty_input_produces_zero_counts_and_no_groups():
    report = build_analytical_report([])

    assert report.samples.total == 0
    assert report.samples.role_eligible.populated == 0
    assert report.samples.salary_eligible.populated == 0
    assert report.samples.role_eligible.rate is None
    assert report.samples.salary_eligible.rate is None
    assert report.groups == []


def test_mixed_input_preserves_denominator():
    report = build_analytical_report(rows)

    assert report.samples.total == 3
    assert report.samples.role_eligible.populated == 1
    assert report.samples.role_eligible.total == 3


def test_grouped_role_counts_reconcile_with_eligible_population():
    report = build_analytical_report(rows)

    total_grouped_roles = sum(
        group.role_count for group in report.groups
    )

    assert total_grouped_roles == 1
    assert total_grouped_roles == report.samples.role_eligible.populated


def test_salary_eligibility_excludes_unclassified_roles_from_groups():
    sample_rows = [
        make_row(
            source_id="job-1",
            processing_status=ProcessingStatus.PROCESSED,
            role_family=RoleFamily.DATA_ENGINEERING,
            salary_min=60000,
            salary_max=70000,
        ),
        make_row(
            source_id="job-2",
            processing_status=ProcessingStatus.PROCESSED,
            role_family=RoleFamily.DATA_ENGINEERING,
            salary_min=None,
            salary_max=None,
        ),
        make_row(
            source_id="job-3",
            processing_status=ProcessingStatus.PROCESSED,
            role_family=None,
            salary_min=50000,
            salary_max=60000,
        ),
    ]

    report = build_analytical_report(sample_rows)

    assert report.samples.total == 3
    assert report.samples.role_eligible.populated == 2
    assert report.samples.salary_eligible.populated == 2

    assert sum(group.role_count for group in report.groups) == 2
    assert sum(group.verified_salary_count for group in report.groups) == 1


def test_manually_constructed_report_rejects_invalid_reconciliation():
    samples = AnalyticalSampleSummary(
        total=1,
        role_eligible=CoverageMetric(populated=1, total=1, rate=1.0),
        salary_eligible=CoverageMetric(populated=0, total=1, rate=0.0),
    )

    with pytest.raises(
        ValidationError,
        match="Grouped roles must reconcile with role eligibility",
    ):
        AnalyticalReport(samples=samples, groups=[])


def test_report_rejects_grouped_salary_count_above_salary_population():
    samples = AnalyticalSampleSummary(
        total=1,
        role_eligible=CoverageMetric(
            populated=1, total=1, rate=1.0
        ),
        salary_eligible=CoverageMetric(
            populated=0, total=1, rate=0.0
        ),
    )

    groups = [
        RoleFamilySummary(
            role_family=RoleFamily.DATA_ENGINEERING,
            role_count=1,
            verified_salary_count=1,
        )
    ]

    with pytest.raises(
        ValidationError,
        match="Grouped verified salaries exceed salary eligibility",
    ):
        AnalyticalReport(samples=samples, groups=groups)


def test_report_rejects_too_many_ungrouped_verified_salaries():
    samples = AnalyticalSampleSummary(
        total=3,
        role_eligible=CoverageMetric(populated=2, total=3, rate=2 / 3),
        salary_eligible=CoverageMetric(populated=2, total=3, rate=2 / 3),
    )
    groups = [
        RoleFamilySummary(
            role_family=RoleFamily.DATA_ENGINEERING,
            role_count=2,
            verified_salary_count=0,
        )
    ]

    with pytest.raises(
        ValidationError,
        match="Ungrouped verified salaries exceed rows outside role eligibility",
    ):
        AnalyticalReport(samples=samples, groups=groups)


def test_report_rejects_duplicate_role_families():
    samples = AnalyticalSampleSummary(
        total=2,
        role_eligible=CoverageMetric(populated=2, total=2, rate=1.0),
        salary_eligible=CoverageMetric(populated=0, total=2, rate=0.0),
    )
    group = RoleFamilySummary(
        role_family=RoleFamily.DATA_ENGINEERING,
        role_count=1,
        verified_salary_count=0,
    )

    with pytest.raises(ValidationError, match="Role family groups must be unique"):
        AnalyticalReport(samples=samples, groups=[group, group])


def test_build_report_does_not_mutate_input():
    sample_rows = [
        make_row(
            source_id="job-1",
            processing_status=ProcessingStatus.PROCESSED,
            role_family=RoleFamily.DATA_ENGINEERING,
        )
    ]

    original = [row.model_dump() for row in sample_rows]

    build_analytical_report(sample_rows)

    assert [row.model_dump() for row in sample_rows] == original
