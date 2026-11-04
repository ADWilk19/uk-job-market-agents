from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import Mock
import pytest
import json

from uk_job_market_agents.cli import (
    build_parser,
    main,
    )
from uk_job_market_agents.analytics.batch_summary import BatchSummary


def test_cli_returns_failure_when_jobs_fail(monkeypatch):
    workflow = Mock(
        return_value=(
            [],
            BatchSummary(
                total=3,
                processed=2,
                review_required=0,
                failed=1,
            ),
        )
    )

    monkeypatch.setattr(
        "uk_job_market_agents.cli.run_snapshot_workflow",
        workflow,
    )

    exit_code = main(
        [
            "--snapshot", "snapshot.json",
            "--collected-at", "2026-11-04T09:00:00+00:00",
            "--jobs-out", "jobs.csv",
            "--summary-out", "summary.csv",
            "--mode", "agent",
        ],
        processor=Mock(),
    )

    assert exit_code == 1


def test_cli_parses_required_arguments():
    parser = build_parser()

    args = parser.parse_args([
        "--snapshot", "data/raw/sample.json",
        "--collected-at", "2026-11-04T09:00:00+00:00",
        "--jobs-out", "output/jobs.csv",
        "--summary-out", "output/summary.csv",
        "--mode", "agent",
    ])

    assert args.snapshot == Path("data/raw/sample.json")
    assert args.collected_at == datetime(
        2026, 11, 4, 9, 0, tzinfo=timezone.utc
    )
    assert args.jobs_out == Path("output/jobs.csv")
    assert args.summary_out == Path("output/summary.csv")


def test_cli_parses_timezone_aware_collection_timestamp():
    parser = build_parser()

    args = parser.parse_args([
        "--snapshot", "snapshot.json",
        "--collected-at", "2026-11-04T09:00:00+00:00",
        "--jobs-out", "jobs.csv",
        "--summary-out", "summary.csv",
        "--mode", "agent",
    ])

    assert args.collected_at == datetime(
        2026, 11, 4, 9, 0, tzinfo=timezone.utc
    )


@pytest.mark.parametrize(
    "timestamp",
    [
        "yesterday",
        "2026-11-04",
        "2026-11-04T09:00:00",
        "not-a-timestamp",
    ],
)
def test_cli_rejects_invalid_or_naive_collection_timestamps(timestamp):
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args([
            "--snapshot", "snapshot.json",
            "--collected-at", timestamp,
            "--jobs-out", "jobs.csv",
            "--summary-out", "summary.csv",
            "--mode", "agent",
        ])

    assert exc_info.value.code == 2


@pytest.mark.parametrize(
    "missing_argument",
    [
        "--snapshot",
        "--collected-at",
        "--jobs-out",
        "--summary-out",
        "--mode",
    ],
)
def test_cli_rejects_missing_required_arguments(missing_argument):
    parser = build_parser()

    arguments = [
        "--snapshot", "snapshot.json",
        "--collected-at", "2026-11-04T09:00:00+00:00",
        "--jobs-out", "jobs.csv",
        "--summary-out", "summary.csv",
        "--mode", "agent",
    ]

    arguments = [
        item
        for index, item in enumerate(arguments)
        if arguments[index - 1] != missing_argument
        and item != missing_argument
    ]

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(arguments)

    assert exc_info.value.code == 2


def test_cli_delegates_to_snapshot_workflow(monkeypatch):
    workflow = Mock(
        return_value=(
            [],
            BatchSummary(
                total=0,
                processed=0,
                review_required=0,
                failed=0,
            ),
        )
    )
    monkeypatch.setattr(
        "uk_job_market_agents.cli.run_snapshot_workflow",
        workflow,
    )

    processor = Mock()

    exit_code = main(
        [
            "--snapshot", "snapshot.json",
            "--collected-at", "2026-11-04T09:00:00+00:00",
            "--jobs-out", "jobs.csv",
            "--summary-out", "summary.csv",
            "--mode", "agent",
        ],
        processor=processor,
    )

    assert exit_code == 0

    workflow.assert_called_once_with(
        snapshot_path=Path("snapshot.json"),
        collected_at=datetime(
            2026, 11, 4, 9, 0, tzinfo=timezone.utc
        ),
        processor=processor,
        job_export_path=Path("jobs.csv"),
        summary_export_path=Path("summary.csv"),
    )


def test_cli_selects_agent_processor(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "offline-test-key")
    workflow = Mock(
        return_value=(
            [],
            BatchSummary(
                total=0,
                processed=0,
                review_required=0,
                failed=0,
            ),
        )
    )
    monkeypatch.setattr(
        "uk_job_market_agents.cli.run_snapshot_workflow",
        workflow,
    )

    factory = Mock(return_value=Mock())
    monkeypatch.setattr(
        "uk_job_market_agents.cli.create_processor",
        factory,
    )

    exit_code = main([
        "--snapshot", "snapshot.json",
        "--collected-at", "2026-11-04T09:00:00+00:00",
        "--jobs-out", "jobs.csv",
        "--summary-out", "summary.csv",
        "--mode", "agent",
    ])

    assert exit_code == 0
    factory.assert_called_once_with("agent")

    assert workflow.call_args.kwargs["processor"] is factory.return_value


def test_cli_requires_explicit_processing_mode():
    parser = build_parser()

    arguments = [
        "--snapshot", "snapshot.json",
        "--collected-at", "2026-11-04T09:00:00+00:00",
        "--jobs-out", "jobs.csv",
        "--summary-out", "summary.csv",
    ]

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(arguments)

    assert exc_info.value.code == 2


def test_cli_reports_processing_summary(monkeypatch, capsys):
    workflow = Mock(
        return_value=(
            [],
            BatchSummary(
                total=10,
                processed=7,
                review_required=2,
                failed=1,
            ),
        )
    )

    monkeypatch.setattr(
        "uk_job_market_agents.cli.run_snapshot_workflow",
        workflow,
    )

    exit_code = main(
        [
            "--snapshot", "snapshot.json",
            "--collected-at", "2026-11-04T09:00:00+00:00",
            "--jobs-out", "jobs.csv",
            "--summary-out", "summary.csv",
            "--mode", "agent",
        ],
        processor=Mock(),
    )

    output = capsys.readouterr().out

    assert exit_code == 1
    assert "Total: 10" in output
    assert "Processed: 7" in output
    assert "Review required: 2" in output
    assert "Failed: 1" in output


def test_cli_reports_missing_snapshot_without_traceback(
    monkeypatch, capsys
):
    workflow = Mock(
        side_effect=FileNotFoundError(
            "Snapshot file not found: missing.json"
        )
    )

    monkeypatch.setattr(
        "uk_job_market_agents.cli.run_snapshot_workflow",
        workflow,
    )

    exit_code = main(
        [
            "--snapshot", "missing.json",
            "--collected-at", "2026-11-04T09:00:00+00:00",
            "--jobs-out", "jobs.csv",
            "--summary-out", "summary.csv",
            "--mode", "agent",
        ],
        processor=Mock(),
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Snapshot file not found" in captured.err
    assert "Traceback" not in captured.err


def test_cli_warns_about_agent_api_usage(monkeypatch, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "offline-test-key")
    workflow = Mock(
        return_value=(
            [],
            BatchSummary(
                total=0,
                processed=0,
                review_required=0,
                failed=0,
            ),
        )
    )

    monkeypatch.setattr(
        "uk_job_market_agents.cli.run_snapshot_workflow",
        workflow,
    )

    exit_code = main(
        [
            "--snapshot", "snapshot.json",
            "--collected-at", "2026-11-04T09:00:00+00:00",
            "--jobs-out", "jobs.csv",
            "--summary-out", "summary.csv",
            "--mode", "agent",
        ],
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "may incur API costs" in captured.err

@pytest.mark.parametrize(
    "collision",
    [
        "snapshot_jobs",
        "snapshot_summary",
        "jobs_summary",
    ],
)
def test_cli_rejects_colliding_paths(
    tmp_path, capsys, collision
):
    snapshot = tmp_path / "snapshot.json"
    jobs_out = tmp_path / "jobs.csv"
    summary_out = tmp_path / "summary.csv"

    if collision == "snapshot_jobs":
        jobs_out = snapshot
    elif collision == "snapshot_summary":
        summary_out = snapshot
    elif collision == "jobs_summary":
        jobs_out = summary_out

    snapshot.write_text(json.dumps({"results": []}), encoding="utf-8")

    original_contents = snapshot.read_text(encoding="utf-8")

    processor = Mock()

    exit_code = main(
        [
            "--snapshot", str(snapshot),
            "--collected-at", "2026-11-04T09:00:00+00:00",
            "--jobs-out", str(jobs_out),
            "--summary-out", str(summary_out),
            "--mode", "agent",
        ],
        processor=processor,
    )

    assert exit_code == 2
    assert snapshot.read_text(encoding="utf-8") == original_contents
    assert "paths cannot be the same" in capsys.readouterr().err.lower()
    processor.assert_not_called()

def test_cli_rejects_missing_agent_credentials(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text(json.dumps({"results": []}), encoding="utf-8")

    jobs_out = tmp_path / "jobs.csv"
    summary_out = tmp_path / "summary.csv"

    processor_factory = Mock()
    monkeypatch.setattr(
        "uk_job_market_agents.cli.create_processor",
        processor_factory,
    )

    exit_code = main(
        [
            "--snapshot", str(snapshot),
            "--collected-at", "2026-11-04T09:00:00+00:00",
            "--jobs-out", str(jobs_out),
            "--summary-out", str(summary_out),
            "--mode", "agent",
        ],
    )

    assert exit_code == 2
    assert "OPENAI_API_KEY" in capsys.readouterr().err
    assert not jobs_out.exists()
    assert not summary_out.exists()
    processor_factory.assert_not_called()
