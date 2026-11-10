
"""Tests for deterministic role-family analytical summaries."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from uk_job_market_agents.agents.batch_orchestration import ProcessingStatus
from uk_job_market_agents.analytics.analytical_dataset import (
    select_role_eligible_rows,
    select_salary_eligible_rows,
)
from uk_job_market_agents.analytics.grouped_summary import (
    summarize_by_role_family,
    RoleFamilySummary
)
from uk_job_market_agents.analytics.job_export import JobExportRow
from uk_job_market_agents.models.job_posting import (
    DescriptionCompleteness,
    RoleFamily,
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


def test_groups_count_approved_roles_and_verified_salaries():
    """Role counts and verified salary counts have distinct eligibility."""
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
        make_row(
            "ds-partial",
            role_family=RoleFamily.DATA_SCIENCE,
            salary_min=50000,
        ),
    ]

    groups = summarize_by_role_family(rows)

    assert [
        (group.role_family, group.role_count, group.verified_salary_count)
        for group in groups
    ] == [
        (RoleFamily.DATA_ENGINEERING, 2, 1),
        (RoleFamily.DATA_SCIENCE, 2, 1),
    ]


def test_review_required_and_failed_rows_are_excluded():
    """Unapproved records must never contribute to grouped results."""
    rows = [
        make_row(
            "approved",
            role_family=RoleFamily.DATA_ENGINEERING,
        ),
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
            salary_min=50000,
            salary_max=60000,
        ),
    ]

    groups = summarize_by_role_family(rows)

    assert len(groups) == 1
    assert groups[0].role_family == RoleFamily.DATA_ENGINEERING
    assert groups[0].role_count == 1
    assert groups[0].verified_salary_count == 0


def test_verified_salary_without_approved_role_is_not_grouped():
    """Salary eligibility alone does not establish a role-family group."""
    rows = [
        make_row(
            "unclassified-salary",
            salary_min=45000,
            salary_max=55000,
        ),
        make_row(
            "classified-salary",
            role_family=RoleFamily.DATA_ENGINEERING,
            salary_min=50000,
            salary_max=60000,
        ),
    ]

    assert len(select_salary_eligible_rows(rows)) == 2

    groups = summarize_by_role_family(rows)

    assert len(groups) == 1
    assert groups[0].role_family == RoleFamily.DATA_ENGINEERING
    assert groups[0].verified_salary_count == 1


def test_group_order_is_deterministic():
    """Grouping order must not depend on input advertisement order."""
    rows = [
        make_row("ds", role_family=RoleFamily.DATA_SCIENCE),
        make_row("de", role_family=RoleFamily.DATA_ENGINEERING),
    ]

    forward = summarize_by_role_family(rows)
    reversed_result = summarize_by_role_family(list(reversed(rows)))

    assert forward == reversed_result
    assert [group.role_family for group in forward] == [
        RoleFamily.DATA_ENGINEERING,
        RoleFamily.DATA_SCIENCE,
    ]


def test_group_counts_reconcile_with_eligible_rows():
    """Grouped role counts must reconcile with the selected population."""
    rows = [
        make_row(
            "de",
            role_family=RoleFamily.DATA_ENGINEERING,
            salary_min=40000,
            salary_max=50000,
        ),
        make_row(
            "ds",
            role_family=RoleFamily.DATA_SCIENCE,
        ),
        make_row("unclassified"),
        make_row(
            "review",
            processing_status=ProcessingStatus.REVIEW_REQUIRED,
        ),
    ]

    groups = summarize_by_role_family(rows)
    eligible = select_role_eligible_rows(rows)

    assert sum(group.role_count for group in groups) == len(eligible)
    assert sum(group.verified_salary_count for group in groups) == 1


def test_empty_input_produces_no_groups():
    """An empty dataset must not generate artificial groups."""
    assert summarize_by_role_family([]) == []


def test_grouping_does_not_mutate_input():
    """Analytical aggregation must leave export records unchanged."""
    rows = [
        make_row(
            "de",
            role_family=RoleFamily.DATA_ENGINEERING,
            salary_min=45000,
            salary_max=55000,
        ),
    ]

    before = [row.model_dump() for row in rows]

    summarize_by_role_family(rows)

    assert [row.model_dump() for row in rows] == before


@pytest.mark.parametrize(
    "role_count, salary_count",
    [
        (-1, 0),
        (1, -1),
        (1, 2),
    ],
)
def test_group_summary_rejects_invalid_counts(
    role_count: int,
    salary_count: int,
):
    with pytest.raises(ValidationError):
        RoleFamilySummary(
            role_family=RoleFamily.DATA_ENGINEERING,
            role_count=role_count,
            verified_salary_count=salary_count,
        )
