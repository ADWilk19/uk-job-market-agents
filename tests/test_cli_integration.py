
import csv
import json
import socket

import pytest

from uk_job_market_agents.agents.batch_orchestration import (
    BatchProcessingOutcome,
    ProcessingStatus,
)
from uk_job_market_agents.cli import main


def test_cli_processes_snapshot_and_writes_exports(tmp_path, capsys):
    snapshot = tmp_path / "snapshot.json"
    jobs_csv = tmp_path / "jobs.csv"
    summary_csv = tmp_path / "summary.csv"

    snapshot.write_text(
        json.dumps({
            "results": [{
                "id": "101",
                "title": "Data Engineer",
                "description": "Python and SQL engineering role",
                "company": {"display_name": "Example Ltd"},
            }]
        }),
        encoding="utf-8",
    )

    def processor(postings):
        assert len(postings) == 1
        assert postings[0].source_id == "101"

        return [
            BatchProcessingOutcome(
                job_id="101",
                status=ProcessingStatus.FAILED,
                error="Simulated processing failure",
            )
        ]

    exit_code = main(
        [
            "--snapshot", str(snapshot),
            "--collected-at", "2026-11-04T09:00:00+00:00",
            "--jobs-out", str(jobs_csv),
            "--summary-out", str(summary_csv),
            "--mode", "agent",
        ],
        processor=processor,
    )

    assert exit_code == 1
    assert jobs_csv.exists()
    assert summary_csv.exists()

    with jobs_csv.open(newline="", encoding="utf-8") as file:
        jobs = list(csv.DictReader(file))

    with summary_csv.open(newline="", encoding="utf-8") as file:
        summaries = list(csv.DictReader(file))

    assert len(jobs) == 1
    assert jobs[0]["source_id"] == "101"
    assert jobs[0]["processing_status"] == "failed"

    assert summaries[0]["total"] == "1"
    assert summaries[0]["failed"] == "1"

    output = capsys.readouterr().out
    assert "Total: 1" in output
    assert "Failed: 1" in output


def test_agent_cli_without_credentials_fails_before_processing(
    tmp_path, monkeypatch, capsys
):

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_ADMIN_KEY", raising=False)

    def reject_request(*args, **kwargs):
        pytest.fail("Missing credentials must fail before an HTTP request")

    monkeypatch.setattr(socket.socket, "connect", reject_request)
    monkeypatch.setattr(socket, "create_connection", reject_request)

    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text(
        json.dumps({
            "results": [
                {
                    "id": str(i),
                    "title": "Data Engineer",
                    "description": "Python and SQL",
                }
                for i in range(2)
            ]
        }),
        encoding="utf-8",
    )

    jobs_csv = tmp_path / "jobs.csv"
    summary_csv = tmp_path / "summary.csv"

    exit_code = main([
        "--snapshot", str(snapshot),
        "--collected-at", "2026-11-04T09:00:00+00:00",
        "--jobs-out", str(jobs_csv),
        "--summary-out", str(summary_csv),
        "--mode", "agent",
    ])

    assert exit_code == 2
    assert not jobs_csv.exists()
    assert not summary_csv.exists()

    captured = capsys.readouterr()
    assert "OPENAI_API_KEY" in captured.err
    assert "Execution error:" not in captured.err


@pytest.mark.parametrize("missing_field", ["id", "title", "description"])
def test_cli_rejects_missing_advert_fields_before_processing(
    tmp_path, capsys, monkeypatch, missing_field
):
    advertisement = {"id": "101", "title": "Engineer", "description": "Python"}
    malformed = dict(advertisement)
    del malformed[missing_field]
    snapshot = tmp_path / "snapshot.json"
    original = json.dumps({"results": [advertisement, malformed]})
    snapshot.write_text(original, encoding="utf-8")
    jobs = tmp_path / "jobs.csv"
    summary = tmp_path / "summary.csv"

    def reject_processing(*args, **kwargs):
        pytest.fail("Malformed snapshots must fail before processing or network access")

    monkeypatch.setattr(socket.socket, "connect", reject_processing)
    monkeypatch.setattr(socket, "create_connection", reject_processing)
    exit_code = main([
        "--snapshot", str(snapshot),
        "--collected-at", "2026-11-04T09:00:00+00:00",
        "--jobs-out", str(jobs),
        "--summary-out", str(summary),
        "--mode", "agent",
    ], processor=reject_processing)

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == ""
    assert captured.err == (
        "Execution error: Invalid Adzuna snapshot: results[1] "
        f"missing required advert fields: {missing_field}\n"
    )
    assert "Traceback" not in captured.err
    assert not jobs.exists()
    assert not summary.exists()
    assert snapshot.read_text(encoding="utf-8") == original
