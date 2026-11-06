
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from uk_job_market_agents.agents.batch_orchestration import ProcessingStatus
from uk_job_market_agents.analytics.data_quality import (
    CoverageMetric,
    DataQualitySummary,
    summarize_data_quality,
)
from uk_job_market_agents.analytics.job_export import JobExportRow
from uk_job_market_agents.models.job_posting import (
    DescriptionCompleteness,
    RoleFamily,
    WorkPattern,
)


COLLECTED_AT = datetime(2026, 11, 5, 9, 42, 31, tzinfo=timezone.utc)


def make_row(source_id: str, **overrides) -> JobExportRow:
    """Build a synthetic export row without invoking agents."""
    values = {
        "source": "adzuna",
        "source_id": source_id,
        "collected_at": COLLECTED_AT,
        "description_completeness": DescriptionCompleteness.EXCERPT,
        "processing_status": ProcessingStatus.PROCESSED,
    }
    values.update(overrides)
    return JobExportRow(**values)


def test_lesson28_quality_metrics():
    """Reproduce the five-record live-run export characteristics."""
    rows = [
        make_row(
            "1",
            processing_status=ProcessingStatus.REVIEW_REQUIRED,
            classification_review_reason="work_pattern",
            company_name="Ocho",
            source_salary_min=60000,
            source_salary_max=60000,
        ),
        make_row(
            "2",
            company_name="VANRATH",
            role_family=RoleFamily.DATA_ENGINEERING,
            work_pattern=WorkPattern.HYBRID,
            source_salary_min=50000,
            source_salary_max=50000,
        ),
        make_row(
            "3",
            company_name="VANRATH",
            role_family=RoleFamily.DATA_ENGINEERING,
            work_pattern=WorkPattern.HYBRID,
            source_salary_min=45000,
            source_salary_max=45000,
        ),
        make_row(
            "4",
            company_name="Anson McCade",
            role_family=RoleFamily.DATA_ENGINEERING,
            work_pattern=WorkPattern.HYBRID,
            source_salary_min=60000,
            source_salary_max=60000,
        ),
        make_row(
            "5",
            company_name="Ocho",
            role_family=RoleFamily.DATA_ENGINEERING,
            work_pattern=WorkPattern.UNKNOWN,
            source_salary_min=60000,
            source_salary_max=60000,
        ),
    ]

    summary = summarize_data_quality(rows)

    assert summary.total == 5
    assert summary.company_coverage == CoverageMetric(
        populated=5, total=5, rate=1.0
    )
    assert summary.approved_role_coverage == CoverageMetric(
        populated=4, total=5, rate=0.8
    )
    assert summary.known_work_pattern_coverage == CoverageMetric(
        populated=3, total=5, rate=0.6
    )
    assert summary.provider_salary_coverage == CoverageMetric(
        populated=5, total=5, rate=1.0
    )
    assert summary.verified_salary_coverage == CoverageMetric(
        populated=0, total=5, rate=0.0
    )
    assert summary.complete_description_coverage == CoverageMetric(
        populated=0, total=5, rate=0.0
    )


def test_empty_dataset_has_undefined_rates():
    summary = summarize_data_quality([])

    assert summary.total == 0
    for name in DataQualitySummary.model_fields:
        if name == "total":
            continue
        metric = getattr(summary, name)
        assert metric.populated == 0
        assert metric.total == 0
        assert metric.rate is None


def test_missing_and_partial_values_do_not_count_as_covered():
    rows = [
        make_row(
            "1",
            company_name=None,
            source_salary_min=50000,
            source_salary_max=None,
            salary_min=40000,
            salary_max=None,
        ),
        make_row(
            "2",
            company_name="   ",
            source_salary_min=None,
            source_salary_max=60000,
        ),
    ]

    summary = summarize_data_quality(rows)

    assert summary.company_coverage.populated == 0
    assert summary.provider_salary_coverage.populated == 0
    assert summary.verified_salary_coverage.populated == 0


def test_unknown_work_pattern_is_not_known_coverage():
    rows = [
        make_row("1", work_pattern=WorkPattern.UNKNOWN),
        make_row("2", work_pattern=WorkPattern.REMOTE),
        make_row("3", work_pattern=None),
    ]

    summary = summarize_data_quality(rows)
    metric = summary.known_work_pattern_coverage

    assert metric.populated == 1
    assert metric.total == 3
    assert metric.rate == pytest.approx(1 / 3)


def test_coverage_metric_rejects_invalid_counts_and_rates():
    with pytest.raises(ValidationError):
        CoverageMetric(populated=3, total=2, rate=1.5)

    with pytest.raises(ValidationError):
        CoverageMetric(populated=-1, total=2, rate=-0.5)


def test_coverage_metric_requires_consistent_rate():
    with pytest.raises(ValidationError):
        CoverageMetric(populated=1, total=2, rate=0.9)

    with pytest.raises(ValidationError):
        CoverageMetric(populated=0, total=0, rate=0.0)



def test_data_quality_summary_rejects_inconsistent_denominators():
    """All coverage metrics must use the summary's total."""
    summary = summarize_data_quality([
        make_row("1", company_name="Example Ltd"),
        make_row("2", company_name=None),
    ])

    values = summary.model_dump()
    values["company_coverage"] = {
        "populated": 1,
        "total": 3,
        "rate": 1 / 3,
    }

    with pytest.raises(
        ValidationError,
        match="Coverage denominator must match summary total",
    ):
        DataQualitySummary.model_validate(values)
