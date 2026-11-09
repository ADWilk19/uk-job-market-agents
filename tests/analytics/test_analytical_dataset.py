
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from uk_job_market_agents.agents.batch_orchestration import ProcessingStatus
from uk_job_market_agents.analytics.analytical_dataset import (
    AnalyticalSampleSummary,
    select_role_eligible_rows,
    select_salary_eligible_rows,
    summarize_analytical_samples,
)
from uk_job_market_agents.analytics.data_quality import CoverageMetric
from uk_job_market_agents.analytics.job_export import JobExportRow
from uk_job_market_agents.models.job_posting import (
    DescriptionCompleteness,
    RoleFamily,
    WorkPattern,
)


COLLECTED_AT = datetime(2026, 11, 5, tzinfo=timezone.utc)


def make_row(source_id: str, **overrides) -> JobExportRow:
    """Create a synthetic export row without invoking agents."""
    values = {
        "source": "adzuna",
        "source_id": source_id,
        "collected_at": COLLECTED_AT,
        "description_completeness": DescriptionCompleteness.EXCERPT,
        "processing_status": ProcessingStatus.PROCESSED,
    }
    values.update(overrides)
    return JobExportRow(**values)


def test_select_role_eligible_rows_excludes_unapproved_records():
    """Only processed records with approved roles are eligible."""
    rows = [
        make_row(
            "approved",
            role_family=RoleFamily.DATA_ENGINEERING,
            work_pattern=WorkPattern.HYBRID,
        ),
        make_row(
            "review",
            processing_status=ProcessingStatus.REVIEW_REQUIRED,
        ),
        make_row(
            "failed",
            processing_status=ProcessingStatus.FAILED,
        ),
        make_row("missing-role"),
    ]

    selected = select_role_eligible_rows(rows)

    assert [row.source_id for row in selected] == ["approved"]


def test_select_salary_eligible_rows_requires_verified_bounds():
    """Provider-only, partial and unapproved salaries are excluded."""
    rows = [
        make_row(
            "verified",
            role_family=RoleFamily.DATA_ENGINEERING,
            salary_min=45000,
            salary_max=55000,
        ),
        make_row(
            "provider-only",
            role_family=RoleFamily.DATA_ENGINEERING,
            source_salary_min=50000,
            source_salary_max=60000,
            source_salary_predicted=True,
        ),
        make_row(
            "partial",
            role_family=RoleFamily.DATA_ENGINEERING,
            salary_min=40000,
            salary_max=None,
        ),
        make_row(
            "review",
            processing_status=ProcessingStatus.REVIEW_REQUIRED,
            salary_min=50000,
            salary_max=60000,
        ),
        make_row(
            "failed",
            processing_status=ProcessingStatus.FAILED,
            salary_min=50000,
            salary_max=60000,
        ),
    ]

    selected = select_salary_eligible_rows(rows)

    assert [row.source_id for row in selected] == ["verified"]



def test_empty_dataset_produces_empty_selections():
    """Empty inputs must not generate synthetic observations."""
    assert select_role_eligible_rows([]) == []
    assert select_salary_eligible_rows([]) == []


def test_selection_preserves_input_order():
    """Filtering must retain the original observation order."""
    rows = [
        make_row(
            "first",
            role_family=RoleFamily.DATA_ENGINEERING,
            salary_min=40000,
            salary_max=50000,
        ),
        make_row(
            "excluded",
            processing_status=ProcessingStatus.REVIEW_REQUIRED,
        ),
        make_row(
            "third",
            role_family=RoleFamily.DATA_SCIENCE,
            salary_min=55000,
            salary_max=65000,
        ),
    ]

    role_rows = select_role_eligible_rows(rows)
    salary_rows = select_salary_eligible_rows(rows)

    assert [row.source_id for row in role_rows] == [
        "first",
        "third",
    ]
    assert [row.source_id for row in salary_rows] == [
        "first",
        "third",
    ]


def test_selection_does_not_mutate_input():
    """Analytical selection must not modify exported records."""
    rows = [
        make_row(
            "approved",
            role_family=RoleFamily.DATA_ENGINEERING,
            salary_min=45000,
            salary_max=55000,
        ),
        make_row(
            "unapproved",
            processing_status=ProcessingStatus.REVIEW_REQUIRED,
        ),
    ]

    before = [row.model_dump() for row in rows]

    select_role_eligible_rows(rows)
    select_salary_eligible_rows(rows)

    assert [row.model_dump() for row in rows] == before
    assert len(rows) == 2



def test_analytical_sample_summary_uses_full_population():
    """Each eligibility rate uses all exported advertisements."""
    rows = [
        make_row(
            "verified",
            role_family=RoleFamily.DATA_ENGINEERING,
            salary_min=45000,
            salary_max=55000,
        ),
        make_row(
            "role-only",
            role_family=RoleFamily.DATA_SCIENCE,
            source_salary_min=50000,
            source_salary_max=60000,
        ),
        make_row(
            "review",
            processing_status=ProcessingStatus.REVIEW_REQUIRED,
        ),
        make_row(
            "failed",
            processing_status=ProcessingStatus.FAILED,
        ),
    ]

    summary = summarize_analytical_samples(rows)

    assert summary.total == 4

    assert summary.role_eligible.populated == 2
    assert summary.role_eligible.total == 4
    assert summary.role_eligible.rate == 0.5

    assert summary.salary_eligible.populated == 1
    assert summary.salary_eligible.total == 4
    assert summary.salary_eligible.rate == 0.25


def test_empty_analytical_sample_summary():
    """Empty datasets have undefined eligibility rates."""
    summary = summarize_analytical_samples([])

    assert summary.total == 0

    assert summary.role_eligible.populated == 0
    assert summary.role_eligible.total == 0
    assert summary.role_eligible.rate is None

    assert summary.salary_eligible.populated == 0
    assert summary.salary_eligible.total == 0
    assert summary.salary_eligible.rate is None



def test_analytical_sample_summary_rejects_mismatched_denominators():
    """Eligibility metrics must use the complete dataset denominator."""
    with pytest.raises(
        ValidationError,
        match="Eligibility denominator must match summary total",
    ):
        AnalyticalSampleSummary(
            total=4,
            role_eligible=CoverageMetric(
                populated=2,
                total=4,
                rate=0.5,
            ),
            salary_eligible=CoverageMetric(
                populated=1,
                total=2,
                rate=0.5,
            ),
        )
