"""Reconcile source advertisements through production analytical reporting."""

import csv

import pytest

from examples.synthetic_scenarios import (
    build_synthetic_postings,
    controlled_classification,
    controlled_salary_extraction,
)
from uk_job_market_agents.agents.batch_orchestration import (
    ProcessingStatus,
    process_jobs,
)

from uk_job_market_agents.agents.salary_review import (
    SalaryReviewStatus,
)
from uk_job_market_agents.agents.workflow import ReviewReason
from uk_job_market_agents.analytics.analytical_dataset import (
    select_role_eligible_rows,
    select_salary_eligible_rows,
)
from uk_job_market_agents.analytics.analytical_report import (
    build_analytical_report,
)
from uk_job_market_agents.analytics.analytical_report_csv import (
    write_analytical_report_csv,
)
from uk_job_market_agents.analytics.job_export import (
    build_job_export_rows,
)
from uk_job_market_agents.models.job_posting import (
    DescriptionCompleteness,
    JobPosting,
    RoleFamily,
    WorkPattern,
)
from uk_job_market_agents.models.salary import (
    SalaryPeriod,
)


@pytest.fixture
def postings() -> list[JobPosting]:
    return build_synthetic_postings()


@pytest.fixture
def controlled_agents(postings):
    classification_calls = []
    salary_calls = []

    source_ids = {
        posting.raw_description: posting.source_id
        for posting in postings
    }

    def fake_classify(job):
        assert job.raw_title == "Data Engineer"

        classification_calls.append(job.source_id)

        return controlled_classification(job.source_id)

    def fake_extract(description):
        source_id = source_ids[description]
        salary_calls.append(source_id)

        return controlled_salary_extraction(source_id)

    return (
        fake_classify,
        fake_extract,
        classification_calls,
        salary_calls,
    )


def test_processing_reconciliation(
    postings,
    controlled_agents,
    tmp_path,
):
    assert len(postings) == 6
    assert len({posting.source_id for posting in postings}) == 6

    assert all(
        posting.source == "synthetic"
        for posting in postings
    )

    assert sum(
        posting.description_completeness
        == DescriptionCompleteness.COMPLETE
        for posting in postings
    ) == 5

    (
        classifier,
        salary_extractor,
        classification_calls,
        salary_calls,
    ) = controlled_agents

    outcomes = process_jobs(
        postings,
        classifier=classifier,
        salary_extractor=salary_extractor,
    )

    assert len(outcomes) == len(postings)

    assert [outcome.job_id for outcome in outcomes] == [
        posting.source_id for posting in postings
    ]

    by_id = {
        outcome.job_id: outcome
        for outcome in outcomes
    }

    assert [outcome.status for outcome in outcomes] == [
        ProcessingStatus.PROCESSED,
        ProcessingStatus.PROCESSED,
        ProcessingStatus.PROCESSED,
        ProcessingStatus.PROCESSED,
        ProcessingStatus.REVIEW_REQUIRED,
        ProcessingStatus.FAILED,
    ]

    assert classification_calls == [
        posting.source_id for posting in postings
    ]

    assert salary_calls == [
        "annual",
        "daily",
        "ambiguous",
    ]

    assert (
        by_id["annual"].result.salary_assessment.status
        == SalaryReviewStatus.VERIFIED
    )

    assert (
        by_id["daily"].result.salary_assessment.status
        == SalaryReviewStatus.VERIFIED
    )

    assert (
        by_id["ambiguous"].result.salary_assessment.status
        == SalaryReviewStatus.REVIEW_REQUIRED
    )

    # Salary review must not become classification review or remove the role.
    ambiguous = by_id["ambiguous"].result
    assert ambiguous.classification.requires_review is False
    assert ambiguous.classification.review_reason is None
    assert ambiguous.salary_assessment.reason == "Unsupported salary evidence format"
    assert ambiguous.analytical_record.salary_min is None
    assert ambiguous.analytical_record.salary_max is None

    expected_quotes = {
        "annual": (60000, 70000, SalaryPeriod.YEAR, "£60,000 - £70,000 per year"),
        "daily": (450, 500, SalaryPeriod.DAY, "£450 - £500 per day"),
        "ambiguous": (55000, 65000, SalaryPeriod.YEAR, "£55,000 - £65,000"),
    }
    for source_id, expected in expected_quotes.items():
        extraction = by_id[source_id].result.salary_assessment.extraction
        quote = extraction.salary
        assert (quote.salary_min, quote.salary_max, quote.period, extraction.evidence) == expected

    assert by_id["excerpt"].result.salary_assessment is None
    assert by_id["review"].result.classification.requires_review is True
    assert by_id["review"].result.classification.review_reason == ReviewReason.ROLE_FAMILY
    assert by_id["review"].result.classification.resolved is None

    assert by_id["review"].result.analytical_record is None
    assert by_id["review"].result.salary_assessment is None

    assert by_id["failed"].result is None
    assert by_id["failed"].error == (
        "Synthetic classification failure"
    )

    rows = build_job_export_rows(postings, outcomes)

    assert len(rows) == len(postings)

    assert [row.source_id for row in rows] == [
        posting.source_id for posting in postings
    ]

    rows_by_id = {
        row.source_id: row
        for row in rows
    }

    for posting, outcome, row in zip(
        postings, outcomes, rows, strict=True
    ):
        assert row.source == posting.source
        assert row.collected_at == posting.collected_at
        assert (
            row.description_completeness
            == posting.description_completeness
        )
        assert row.processing_status == outcome.status
        assert row.source_salary_min == posting.source_salary_min
        assert row.source_salary_max == posting.source_salary_max
        assert row.source_salary_predicted == posting.source_salary_predicted
        assert row.classification_review_reason == (
            ReviewReason.ROLE_FAMILY if posting.source_id == "review" else None
        )
        if outcome.result is not None:
            result = outcome.result
            assert result.source_id == posting.source_id
            assert result.source == posting.source
            assert result.source_url == posting.source_url
            assert result.collected_at == posting.collected_at
            assert result.description_completeness == posting.description_completeness

    assert (
        rows_by_id["annual"].salary_min,
        rows_by_id["annual"].salary_max,
    ) == (60000, 70000)

    for source_id in (
        "daily",
        "ambiguous",
        "excerpt",
        "review",
        "failed",
    ):
        assert rows_by_id[source_id].salary_min is None
        assert rows_by_id[source_id].salary_max is None

    for source_id in (
        "annual",
        "daily",
        "ambiguous",
        "excerpt",
    ):
        assert (
            rows_by_id[source_id].role_family
            == RoleFamily.DATA_ENGINEERING
        )
        assert (
            rows_by_id[source_id].work_pattern
            == WorkPattern.REMOTE
        )

    for source_id in ("review", "failed"):
        assert rows_by_id[source_id].role_family is None
        assert rows_by_id[source_id].work_pattern is None

    excerpt = rows_by_id["excerpt"]

    assert excerpt.source_salary_min == 50000
    assert excerpt.source_salary_max == 60000
    assert excerpt.source_salary_predicted is True

    assert [row.source_id for row in select_role_eligible_rows(rows)] == [
        "annual", "daily", "ambiguous", "excerpt",
    ]
    assert [row.source_id for row in select_salary_eligible_rows(rows)] == ["annual"]

    report = build_analytical_report(rows)

    assert report.samples.total == 6

    assert report.samples.role_eligible.populated == 4
    assert report.samples.salary_eligible.populated == 1
    assert report.samples.role_eligible.total == len(postings)
    assert report.samples.salary_eligible.total == len(postings)
    assert report.samples.role_eligible.rate == pytest.approx(4 / 6)
    assert report.samples.salary_eligible.rate == pytest.approx(1 / 6)

    assert len(report.groups) == 1

    group = report.groups[0]

    assert group.role_family == RoleFamily.DATA_ENGINEERING
    assert group.role_count == 4
    assert group.verified_salary_count == 1

    assert sum(
        group.role_count
        for group in report.groups
    ) == report.samples.role_eligible.populated

    assert sum(
        group.verified_salary_count
        for group in report.groups
    ) == report.samples.salary_eligible.populated

    samples_path = tmp_path / "samples.csv"
    groups_path = tmp_path / "groups.csv"

    write_analytical_report_csv(
        report,
        samples_path,
        groups_path,
    )

    with samples_path.open(
        encoding="utf-8", newline=""
    ) as file:
        samples = list(csv.DictReader(file))

    with groups_path.open(
        encoding="utf-8", newline=""
    ) as file:
        groups = list(csv.DictReader(file))

    assert len(samples) == 1
    assert len(groups) == 1

    sample = samples[0]
    group = groups[0]

    assert int(sample["total"]) == 6
    assert int(sample["role_eligible"]) == 4
    assert int(sample["salary_eligible"]) == 1

    assert float(
        sample["role_eligible_rate"]
    ) == pytest.approx(4 / 6)

    assert float(
        sample["salary_eligible_rate"]
    ) == pytest.approx(1 / 6)

    assert group["role_family"] == "data_engineering"
    assert int(group["role_count"]) == 4
    assert int(group["verified_salary_count"]) == 1

    assert float(
        group["verified_salary_rate"]
    ) == pytest.approx(1 / 4)
