import socket
import pytest
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from uk_job_market_agents.agents.batch_orchestration import (
    BatchProcessingOutcome,
    ProcessingStatus,
)
from uk_job_market_agents.agents.orchestration import (
    OrchestrationResult,
)
from uk_job_market_agents.agents.workflow import (
    ResolvedClassification,
    WorkflowResolution,
)
from uk_job_market_agents.analytics.models import AnalyticalJobRecord
from uk_job_market_agents.ingestion.snapshot_execution import (
    run_snapshot_workflow,
)
from uk_job_market_agents.models.job_posting import (
    RoleFamily,
    WorkPattern,
)


def test_run_snapshot_workflow_composes_existing_pipeline(tmp_path):
    """Prepare snapshot postings and delegate to the offline workflow."""
    snapshot_path = tmp_path / "snapshot.json"
    job_export_path = tmp_path / "jobs.csv"
    summary_export_path = tmp_path / "summary.csv"

    collected_at = datetime(
        2026, 10, 26, 10, 0, tzinfo=timezone.utc
    )

    postings = [Mock()]
    processor = Mock()
    expected_outcomes = [Mock()]
    expected_summary = Mock()

    with (
        patch(
            "uk_job_market_agents.ingestion.snapshot_execution.prepare_adzuna_snapshot",
            return_value=postings,
        ) as prepare,
        patch(
            "uk_job_market_agents.ingestion.snapshot_execution.run_offline_workflow",
            return_value=(expected_outcomes, expected_summary),
        ) as execute,
    ):
        result = run_snapshot_workflow(
            snapshot_path,
            collected_at=collected_at,
            processor=processor,
            job_export_path=job_export_path,
            summary_export_path=summary_export_path,
        )

    prepare.assert_called_once_with(
        snapshot_path,
        collected_at=collected_at,
    )

    execute.assert_called_once_with(
        postings,
        processor=processor,
        job_export_path=job_export_path,
        summary_export_path=summary_export_path,
    )

    assert result == (expected_outcomes, expected_summary)


def test_run_snapshot_workflow_empty_snapshot(tmp_path):
    """An empty snapshot produces both CSV exports."""
    snapshot_path = tmp_path / "snapshot.json"
    snapshot_path.write_text(
        json.dumps({"results": []}),
        encoding="utf-8",
    )

    job_export_path = tmp_path / "jobs.csv"
    summary_export_path = tmp_path / "summary.csv"

    processor = Mock(return_value=[])

    outcomes, summary = run_snapshot_workflow(
        snapshot_path,
        collected_at=datetime(
            2026, 10, 26, 10, 0, tzinfo=timezone.utc
        ),
        processor=processor,
        job_export_path=job_export_path,
        summary_export_path=summary_export_path,
    )

    processor.assert_called_once_with([])
    assert outcomes == []
    assert summary.total == 0
    assert summary.processed == 0
    assert summary.review_required == 0
    assert summary.failed == 0

    assert job_export_path.exists()
    assert summary_export_path.exists()


def test_run_snapshot_workflow_preserves_failed_job_provenance(tmp_path):
    """Deduplicate snapshot adverts and preserve metadata on failure."""
    snapshot_path = tmp_path / "snapshot.json"

    advertisement = {
        "id": "101",
        "title": "Data Engineer",
        "description": "Python and SQL engineering role",
        "company": {"display_name": "Example Ltd"},
        "salary_min": 40000,
        "salary_max": 60000,
        "salary_is_predicted": "1",
    }

    snapshot_path.write_text(
        json.dumps({"results": [advertisement, advertisement]}),
        encoding="utf-8",
    )

    collected_at = datetime(
        2026, 10, 26, 10, 0, tzinfo=timezone.utc
    )

    job_export_path = tmp_path / "jobs.csv"
    summary_export_path = tmp_path / "summary.csv"

    def processor(postings):
        assert len(postings) == 1
        assert postings[0].source_id == "101"
        assert postings[0].collected_at == collected_at

        return [
            BatchProcessingOutcome(
                job_id="101",
                status=ProcessingStatus.FAILED,
                error="Simulated offline failure",
            )
        ]

    outcomes, summary = run_snapshot_workflow(
        snapshot_path,
        collected_at=collected_at,
        processor=processor,
        job_export_path=job_export_path,
        summary_export_path=summary_export_path,
    )

    assert len(outcomes) == 1
    assert summary.total == 1
    assert summary.failed == 1

    with job_export_path.open(
        newline="", encoding="utf-8"
    ) as source:
        rows = list(csv.DictReader(source))

    assert len(rows) == 1

    row = rows[0]

    assert row["source"] == "adzuna"
    assert row["source_id"] == "101"
    assert row["collected_at"] == "2026-10-26T10:00:00Z"
    assert row["processing_status"] == "failed"
    assert row["description_completeness"] == "excerpt"
    assert row["company_name"] == "Example Ltd"

    # Provider salary metadata is retained.
    assert row["source_salary_min"] == "40000.0"
    assert row["source_salary_max"] == "60000.0"

    # Provider values must not become verified salaries.
    assert row["salary_min"] == ""
    assert row["salary_max"] == ""

    with summary_export_path.open(
        newline="", encoding="utf-8"
    ) as source:
        summary_rows = list(csv.DictReader(source))

    assert len(summary_rows) == 1
    assert summary_rows[0]["total"] == "1"
    assert summary_rows[0]["failed"] == "1"


def test_run_snapshot_workflow_exports_processed_job(tmp_path):
    """Export a processed job without promoting provider salary."""
    snapshot_path = tmp_path / "snapshot.json"

    advertisement = {
        "id": "201",
        "title": "Analytics Engineer",
        "description": "Build analytical models using SQL and Python.",
        "salary_min": 45000,
        "salary_max": 65000,
    }

    snapshot_path.write_text(
        json.dumps({"results": [advertisement]}),
        encoding="utf-8",
    )

    def processor(postings):
        assert len(postings) == 1

        return [
            BatchProcessingOutcome(
                job_id=postings[0].source_id,
                status=ProcessingStatus.PROCESSED,
                result=OrchestrationResult(
                    classification=WorkflowResolution(
                        resolved=ResolvedClassification(
                            role_family=RoleFamily.ANALYTICS_ENGINEERING,
                            work_pattern=WorkPattern.REMOTE,
                        ),
                        requires_review=False,
                        review_reason=None,
                    ),
                    analytical_record=AnalyticalJobRecord(
                        title=postings[0].raw_title,
                        role_family=RoleFamily.ANALYTICS_ENGINEERING,
                        work_pattern=WorkPattern.REMOTE,
                        salary_min=None,
                        salary_max=None,
                    ),
                ),
            )
        ]

    job_export_path = tmp_path / "jobs.csv"
    summary_export_path = tmp_path / "summary.csv"

    _, summary = run_snapshot_workflow(
        snapshot_path,
        collected_at=datetime(
            2026, 10, 26, 10, 0, tzinfo=timezone.utc
        ),
        processor=processor,
        job_export_path=job_export_path,
        summary_export_path=summary_export_path,
    )

    assert summary.total == 1
    assert summary.processed == 1
    assert summary.failed == 0

    with job_export_path.open(
        newline="", encoding="utf-8"
    ) as source:
        rows = list(csv.DictReader(source))

    assert len(rows) == 1
    row = rows[0]

    assert row["source_id"] == "201"
    assert row["processing_status"] == "processed"
    assert row["role_family"] == "analytics_engineering"
    assert row["work_pattern"] == "remote"

    assert row["source_salary_min"] == "45000.0"
    assert row["source_salary_max"] == "65000.0"
    assert row["salary_min"] == ""
    assert row["salary_max"] == ""


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    """Fail any test that attempts a network connection."""

    def blocked(*args, **kwargs):
        pytest.fail("Snapshot workflow attempted a network connection")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
