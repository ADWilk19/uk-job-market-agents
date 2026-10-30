import csv
import socket
from datetime import datetime, timezone

import pytest

from uk_job_market_agents.agents.batch_orchestration import BatchProcessingOutcome, ProcessingStatus
from uk_job_market_agents.agents.orchestration import OrchestrationResult
from uk_job_market_agents.agents.workflow import ResolvedClassification, ReviewReason, WorkflowResolution
from uk_job_market_agents.analytics.job_export_csv import JOB_EXPORT_COLUMNS
from uk_job_market_agents.analytics.models import AnalyticalJobRecord
from uk_job_market_agents.ingestion.offline_workflow import run_offline_workflow
from uk_job_market_agents.models.job_posting import DescriptionCompleteness, JobPosting, RoleFamily, WorkPattern


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    def blocked(*args, **kwargs):
        pytest.fail("Offline workflow attempted a network connection")
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)


def posting(job_id):
    return JobPosting(
        source="adzuna", source_id=job_id, raw_title="Data Engineer",
        raw_description="Python and SQL", company_name="Café, Ltd",
        collected_at=datetime(2026, 10, 30, tzinfo=timezone.utc),
        description_completeness=DescriptionCompleteness.EXCERPT,
        source_salary_min=40000.0, source_salary_max=60000.0,
        source_salary_predicted=True,
    )


def failed(job_id):
    return BatchProcessingOutcome(job_id=job_id, status=ProcessingStatus.FAILED, error="Fixture failure")


def test_empty_batch(tmp_path):
    jobs, metrics = tmp_path / "jobs.csv", tmp_path / "summary.csv"
    calls = []

    def processor(postings):
        calls.append(postings)
        return []

    outcomes, summary = run_offline_workflow([], processor=processor, job_export_path=jobs, summary_export_path=metrics)
    assert calls == [[]]
    assert outcomes == []
    assert summary.total == 0
    assert jobs.read_bytes() == (",".join(JOB_EXPORT_COLUMNS) + "\n").encode()
    assert metrics.read_bytes() == (
        b"total,processed,review_required,failed,processed_rate,review_rate,failure_rate\n"
        b"0,0,0,0,0.000000,0.000000,0.000000\n"
    )


@pytest.mark.parametrize("verified_salary", [False, True])
def test_mixed_batch_preserves_provenance_and_is_repeatable(tmp_path, verified_salary):
    postings = [posting(str(i)) for i in range(3)]
    record = AnalyticalJobRecord(
        title="Data Engineer", role_family=RoleFamily.DATA_ENGINEERING,
        work_pattern=WorkPattern.HYBRID,
        salary_min=45000 if verified_salary else None,
        salary_max=55000 if verified_salary else None,
    )
    expected = [
        BatchProcessingOutcome(job_id="0", status=ProcessingStatus.PROCESSED, result=OrchestrationResult(
            classification=WorkflowResolution(resolved=ResolvedClassification(
                role_family=RoleFamily.DATA_ENGINEERING, work_pattern=WorkPattern.HYBRID), requires_review=False, review_reason=None),
            analytical_record=record)),
        BatchProcessingOutcome(job_id="1", status=ProcessingStatus.REVIEW_REQUIRED, result=OrchestrationResult(
            classification=WorkflowResolution(resolved=None, requires_review=True, review_reason=ReviewReason.ROLE_FAMILY),
            analytical_record=record)),
        failed("2"),
    ]
    calls = []

    def processor(received):
        assert received is postings
        calls.append(received)
        return expected

    jobs, metrics = tmp_path / "jobs.csv", tmp_path / "summary.csv"
    snapshots = []
    for _ in range(2):
        outcomes, summary = run_offline_workflow(postings, processor=processor, job_export_path=jobs, summary_export_path=metrics)
        assert outcomes is expected
        assert (summary.total, summary.processed, summary.review_required, summary.failed) == (3, 1, 1, 1)
        snapshots.append((jobs.read_bytes(), metrics.read_bytes()))
    assert len(calls) == 2
    assert snapshots[0] == snapshots[1]
    assert b"\r" not in snapshots[0][0]
    assert snapshots[0][1].endswith(b"3,1,1,1,0.333333,0.333333,0.333333\n")
    with jobs.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert [r["source_id"] for r in rows] == ["0", "1", "2"]
    assert [r["processing_status"] for r in rows] == ["processed", "review_required", "failed"]
    for row in rows:
        assert row["source"] == "adzuna"
        assert row["collected_at"] == "2026-10-30T00:00:00Z"
        assert row["description_completeness"] == "excerpt"
        assert row["company_name"] == "Café, Ltd"
        assert (row["source_salary_min"], row["source_salary_max"], row["source_salary_predicted"]) == ("40000.0", "60000.0", "True")
    assert rows[0]["salary_min"] == ("45000" if verified_salary else "")
    assert rows[0]["salary_max"] == ("55000" if verified_salary else "")
    assert rows[0]["role_family"] == "data_engineering"
    for row in rows[1:]:
        assert all(row[field] == "" for field in ("salary_min", "salary_max", "role_family", "work_pattern"))
    assert rows[1]["classification_review_reason"] == ReviewReason.ROLE_FAMILY.value


@pytest.mark.parametrize("ids", [[], ["0", "1"], ["wrong"]])
@pytest.mark.parametrize("existing", [False, True])
def test_mismatch_does_not_write_exports(tmp_path, ids, existing):
    jobs, metrics = tmp_path / "jobs.csv", tmp_path / "summary.csv"
    if existing:
        jobs.write_bytes(b"original jobs")
        metrics.write_bytes(b"original summary")
    with pytest.raises(ValueError):
        run_offline_workflow([posting("0")], processor=lambda _: [failed(i) for i in ids], job_export_path=jobs, summary_export_path=metrics)
    if existing:
        assert jobs.read_bytes() == b"original jobs"
        assert metrics.read_bytes() == b"original summary"
    else:
        assert not jobs.exists() and not metrics.exists()


@pytest.mark.parametrize("alias", ["same", "symlink", "hardlink"])
def test_colliding_outputs_rejected_before_processing(tmp_path, alias):
    jobs = tmp_path / "jobs.csv"
    jobs.write_bytes(b"original")
    metrics = jobs if alias == "same" else tmp_path / "summary.csv"
    if alias == "symlink":
        metrics.symlink_to(jobs)
    elif alias == "hardlink":
        metrics.hardlink_to(jobs)

    def processor(_):
        pytest.fail("Processor must not run for colliding outputs")

    with pytest.raises(ValueError, match="distinct"):
        run_offline_workflow([], processor=processor, job_export_path=jobs, summary_export_path=metrics)
    assert jobs.read_bytes() == b"original"
