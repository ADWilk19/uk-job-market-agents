import importlib.util
import sys
from pathlib import Path

import pytest

from uk_job_market_agents.agents.classifier import (
    ClassificationResult,
)
from uk_job_market_agents.models.job_posting import (
    DescriptionCompleteness,
    JobPosting,
    RoleFamily,
    WorkPattern,
)
from datetime import datetime, timezone


@pytest.fixture
def runner(monkeypatch, tmp_path):
    root = Path(__file__).resolve().parents[2]

    spec = importlib.util.spec_from_file_location(
        "capture_classifications",
        root / "scripts" / "capture_classifications.py",
    )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    monkeypatch.setattr(
        module,
        "CAPTURE_PATH",
        tmp_path / "captures.jsonl",
    )

    return module


@pytest.fixture
def population():
    return [
        JobPosting(
            source="adzuna",
            source_id=str(index),
            collected_at=datetime(
                2026, 11, 16, tzinfo=timezone.utc
            ),
            raw_title=f"Data Engineer {index}",
            raw_description="Fully remote role.",
            description_completeness=(
                DescriptionCompleteness.EXCERPT
            ),
        )
        for index in range(3)
    ]


@pytest.fixture
def classification():
    return ClassificationResult(
        role_family=RoleFamily.DATA_ENGINEERING,
        work_pattern=WorkPattern.REMOTE,
        reasoning="Controlled test response.",
    )


def test_dry_run_makes_no_api_calls(
    runner, population, monkeypatch
):
    monkeypatch.setattr(
        runner, "load_population", lambda: population
    )

    def unexpected_call(*args):
        pytest.fail("Dry run attempted classification")

    monkeypatch.setattr(
        runner, "classify_with_llm", unexpected_call
    )

    monkeypatch.setattr(
        sys, "argv", ["capture_classifications", "--dry-run"]
    )

    runner.main()

    assert not runner.CAPTURE_PATH.exists()


def test_limit_and_resume(
    runner, population, classification, monkeypatch
):
    monkeypatch.setattr(
        runner, "load_population", lambda: population
    )

    calls = []

    def classify(title, description):
        calls.append(title)
        return classification

    monkeypatch.setattr(
        runner, "classify_with_llm", classify
    )

    monkeypatch.setattr(
        sys,
        "argv",
        ["capture_classifications", "--limit", "1"],
    )

    runner.main()

    assert calls == [population[0].raw_title]

    captures = runner.read_classification_captures(
        runner.CAPTURE_PATH
    )

    assert len(captures) == 1

    monkeypatch.setattr(
        sys, "argv", ["capture_classifications", "--all"]
    )

    runner.main()

    assert calls == [
        posting.raw_title for posting in population
    ]

    captures = runner.read_classification_captures(
        runner.CAPTURE_PATH
    )

    assert len(captures) == 3

    # A completed population must not be classified again.
    original_bytes = runner.CAPTURE_PATH.read_bytes()

    runner.main()

    assert len(calls) == 3
    assert runner.CAPTURE_PATH.read_bytes() == original_bytes


def test_interrupted_capture_can_resume(
    runner, population, classification, monkeypatch
):
    monkeypatch.setattr(
        runner, "load_population", lambda: population
    )

    calls = []

    def interrupted_classifier(title, description):
        calls.append(title)

        if len(calls) == 2:
            raise RuntimeError("Simulated API failure")

        return classification

    monkeypatch.setattr(
        runner,
        "classify_with_llm",
        interrupted_classifier,
    )

    monkeypatch.setattr(
        sys, "argv", ["capture_classifications", "--all"]
    )

    with pytest.raises(
        RuntimeError, match="Simulated API failure"
    ):
        runner.main()

    captures = runner.read_classification_captures(
        runner.CAPTURE_PATH
    )

    assert len(captures) == 1
    assert captures[0].source_id == population[0].source_id

    resumed_calls = []

    def resumed_classifier(title, description):
        resumed_calls.append(title)
        return classification

    monkeypatch.setattr(
        runner,
        "classify_with_llm",
        resumed_classifier,
    )

    runner.main()

    assert resumed_calls == [
        posting.raw_title for posting in population[1:]
    ]

    captures = runner.read_classification_captures(
        runner.CAPTURE_PATH
    )

    assert len(captures) == 3


def test_incompatible_checkpoint_blocks_capture(
    runner, population, classification, monkeypatch
):
    monkeypatch.setattr(
        runner, "load_population", lambda: population
    )

    capture = runner.build_classification_capture(
        population[0],
        classification,
        captured_at=datetime.now(timezone.utc),
    )

    incompatible = capture.model_copy(
        update={"input_sha256": "0" * 64}
    )

    runner.append_capture(
        incompatible, runner.CAPTURE_PATH
    )

    original_bytes = runner.CAPTURE_PATH.read_bytes()

    def unexpected_call(*args):
        pytest.fail("Incompatible checkpoint triggered API call")

    monkeypatch.setattr(
        runner, "classify_with_llm", unexpected_call
    )

    monkeypatch.setattr(
        sys, "argv", ["capture_classifications", "--all"]
    )

    with pytest.raises(
        ValueError, match="Classification input mismatch"
    ):
        runner.main()

    assert runner.CAPTURE_PATH.read_bytes() == original_bytes


@pytest.mark.parametrize("checkpoint", ["malformed", "duplicate", "foreign"])
def test_invalid_checkpoint_prevents_calls_and_writes(
    runner, population, classification, monkeypatch, checkpoint
):
    monkeypatch.setattr(runner, "load_population", lambda: population)
    capture = runner.build_classification_capture(
        population[0], classification,
        captured_at=datetime(2026, 11, 26, tzinfo=timezone.utc),
    )
    if checkpoint == "foreign":
        capture = capture.model_copy(update={"source_id": "not-in-population"})
    content = capture.model_dump_json() + "\n"
    if checkpoint == "duplicate":
        content *= 2
    elif checkpoint == "malformed":
        content += '{"source":'
    runner.CAPTURE_PATH.write_text(content, encoding="utf-8")
    original = runner.CAPTURE_PATH.read_bytes()

    def unexpected_call(*args):
        pytest.fail("Invalid checkpoint triggered an API call")

    monkeypatch.setattr(runner, "classify_with_llm", unexpected_call)
    monkeypatch.setattr(sys, "argv", ["capture_classifications", "--all"])
    with pytest.raises(ValueError):
        runner.main()
    assert runner.CAPTURE_PATH.read_bytes() == original


def test_resume_complete_record_without_final_newline(
    runner, population, classification, monkeypatch
):
    monkeypatch.setattr(runner, "load_population", lambda: population)
    capture = runner.build_classification_capture(
        population[0], classification,
        captured_at=datetime(2026, 11, 26, tzinfo=timezone.utc),
    )
    runner.CAPTURE_PATH.write_text(capture.model_dump_json(), encoding="utf-8")
    calls = []

    def classify(title, description):
        calls.append(title)
        return classification

    monkeypatch.setattr(runner, "classify_with_llm", classify)
    monkeypatch.setattr(sys, "argv", ["capture_classifications", "--all"])
    runner.main()
    assert calls == [p.raw_title for p in population[1:]]
    assert len(runner.read_classification_captures(runner.CAPTURE_PATH)) == 3
