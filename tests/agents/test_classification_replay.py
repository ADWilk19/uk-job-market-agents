from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from uk_job_market_agents.agents.batch_orchestration import (
    ProcessingStatus,
    process_jobs,
)
from uk_job_market_agents.agents.classifier import (
    CLASSIFICATION_MODEL,
    ClassificationResult,
    build_classification_prompt,
)
from uk_job_market_agents.agents.classification_replay import (
    ClassificationCapture,
    ClassificationReplay,
    ClassificationReplayError,
    build_classification_capture,
    classification_input_sha256,
    read_classification_captures,
    sha256_text,
    write_classification_captures,
)
from uk_job_market_agents.models.job_posting import (
    DescriptionCompleteness,
    JobPosting,
    RoleFamily,
    WorkPattern,
)


@pytest.fixture
def posting():
    return JobPosting(
        source="synthetic",
        source_id="test-001",
        collected_at=datetime(
            2026, 11, 16, tzinfo=timezone.utc
        ),
        raw_title="Data Engineer",
        raw_description="Fully remote role.",
    )


@pytest.fixture
def classification():
    return ClassificationResult(
        role_family=RoleFamily.DATA_ENGINEERING,
        work_pattern=WorkPattern.REMOTE,
        reasoning="Controlled classification response.",
    )


@pytest.fixture
def capture(posting, classification):
    return build_classification_capture(
        posting,
        classification,
        captured_at=datetime(
            2026, 11, 26, tzinfo=timezone.utc
        ),
    )


def test_sha256_known_value():
    assert sha256_text("abc") == (
        "ba7816bf8f01cfea414140de5dae2223"
        "b00361a396177a9cb410ff61f20015ad"
    )


def test_input_fingerprint_is_deterministic():
    assert classification_input_sha256(
        "Data Engineer", "Fully remote role."
    ) == classification_input_sha256(
        "Data Engineer", "Fully remote role."
    )


@pytest.mark.parametrize(
    "title,description",
    [
        ("Data Scientist", "Fully remote role."),
        ("Data Engineer", "Hybrid role."),
        ("Data Engineer", "Fully remote role. "),
    ],
)
def test_changed_input_changes_fingerprint(
    title, description
):
    original = classification_input_sha256(
        "Data Engineer",
        "Fully remote role.",
    )

    assert classification_input_sha256(
        title, description
    ) != original


def test_capture_preserves_provenance(
    posting, classification, capture
):
    assert capture.source == posting.source
    assert capture.source_id == posting.source_id
    assert capture.classification == classification
    assert capture.model == CLASSIFICATION_MODEL

    assert capture.input_sha256 == (
        classification_input_sha256(
            posting.raw_title,
            posting.raw_description,
        )
    )

    assert capture.prompt_sha256 == sha256_text(
        build_classification_prompt(
            posting.raw_title,
            posting.raw_description,
        )
    )


def test_capture_json_round_trip(capture):
    restored = ClassificationCapture.model_validate_json(
        capture.model_dump_json()
    )

    assert restored == capture


def test_invalid_fingerprint_is_rejected(capture):
    payload = capture.model_dump()
    payload["input_sha256"] = "invalid"

    with pytest.raises(ValidationError):
        ClassificationCapture.model_validate(payload)


def test_invalid_classification_is_rejected(capture):
    payload = capture.model_dump()
    payload["classification"]["role_family"] = "invalid"

    with pytest.raises(ValidationError):
        ClassificationCapture.model_validate(payload)

def test_replay_returns_captured_classification(
    posting, classification, capture
):
    replay = ClassificationReplay([capture])

    assert replay.classify(posting) == classification


def test_missing_capture_is_rejected(posting):
    replay = ClassificationReplay([])

    with pytest.raises(
        ClassificationReplayError,
        match="Missing classification capture",
    ):
        replay.classify(posting)


def test_duplicate_capture_is_rejected(capture):
    with pytest.raises(
        ClassificationReplayError,
        match="Duplicate classification capture",
    ):
        ClassificationReplay([capture, capture])


@pytest.mark.parametrize(
    "changes",
    [
        {"source": "another-provider"},
        {"source_id": "test-002"},
    ],
)
def test_changed_identity_is_rejected(
    posting, capture, changes
):
    replay = ClassificationReplay([capture])
    changed = posting.model_copy(update=changes)

    with pytest.raises(
        ClassificationReplayError,
        match="Missing classification capture",
    ):
        replay.classify(changed)


@pytest.mark.parametrize(
    "changes",
    [
        {"raw_title": "Data Scientist"},
        {"raw_description": "Hybrid role."},
    ],
)
def test_changed_posting_is_rejected(
    posting, capture, changes
):
    replay = ClassificationReplay([capture])
    changed = posting.model_copy(update=changes)

    with pytest.raises(
        ClassificationReplayError,
        match="Classification input mismatch",
    ):
        replay.classify(changed)


@pytest.mark.parametrize(
    "changes,error",
    [
        (
            {"prompt_sha256": "0" * 64},
            "Classification prompt mismatch",
        ),
        (
            {"model": "different-model"},
            "Classification model mismatch",
        ),
    ],
)
def test_incompatible_capture_is_rejected(
    posting, capture, changes, error
):
    incompatible = capture.model_copy(update=changes)
    replay = ClassificationReplay([incompatible])

    with pytest.raises(
        ClassificationReplayError,
        match=error,
    ):
        replay.classify(posting)


def test_replay_result_mutation_is_isolated(
    posting, classification, capture
):
    replay = ClassificationReplay([capture])

    result = replay.classify(posting)
    result.reasoning = "Modified reasoning."

    assert replay.classify(posting) == classification


def test_capture_mutation_is_isolated(
    posting, capture
):
    replay = ClassificationReplay([capture])

    expected = capture.classification.model_copy(
        deep=True
    )

    capture.classification.reasoning = "Modified reasoning."

    assert replay.classify(posting) == expected


def test_production_batch_uses_replay(
    posting, capture
):
    posting = posting.model_copy(
        update={
            "description_completeness":
                DescriptionCompleteness.EXCERPT,
        }
    )

    replay = ClassificationReplay([capture])

    outcomes = process_jobs(
        [posting],
        classifier=replay.classify,
    )

    assert len(outcomes) == 1

    outcome = outcomes[0]

    assert outcome.job_id == posting.source_id
    assert outcome.status == ProcessingStatus.PROCESSED
    assert outcome.result is not None

    record = outcome.result.analytical_record

    assert record is not None
    assert record.role_family == RoleFamily.DATA_ENGINEERING
    assert record.work_pattern == WorkPattern.REMOTE

    assert outcome.result.salary_assessment is None


def test_missing_capture_becomes_failed_outcome(
    posting,
):
    replay = ClassificationReplay([])

    outcomes = process_jobs(
        [posting],
        classifier=replay.classify,
    )

    assert len(outcomes) == 1

    outcome = outcomes[0]

    assert outcome.status == ProcessingStatus.FAILED
    assert outcome.result is None
    assert "Missing classification capture" in outcome.error


def test_capture_file_round_trip(
    posting, capture, tmp_path
):
    path = tmp_path / "captures.jsonl"

    write_classification_captures([capture], path)

    restored = read_classification_captures(path)

    assert restored == [capture]

    replay = ClassificationReplay(restored)

    assert replay.classify(posting) == capture.classification


def test_capture_file_is_deterministic(
    capture, tmp_path
):
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"

    write_classification_captures([capture], first)
    write_classification_captures([capture], second)

    assert first.read_bytes() == second.read_bytes()
    assert first.read_bytes().endswith(b"\n")


def test_existing_capture_file_is_preserved(
    capture, tmp_path
):
    path = tmp_path / "captures.jsonl"
    path.write_bytes(b"existing content\n")

    with pytest.raises(FileExistsError):
        write_classification_captures([capture], path)

    assert path.read_bytes() == b"existing content\n"


def test_duplicate_captures_are_not_written(
    capture, tmp_path
):
    path = tmp_path / "captures.jsonl"

    with pytest.raises(
        ClassificationReplayError,
        match="Duplicate classification capture",
    ):
        write_classification_captures(
            [capture, capture],
            path,
        )

    assert not path.exists()


def test_duplicate_persisted_captures_are_rejected(
    capture, tmp_path
):
    path = tmp_path / "captures.jsonl"

    path.write_text(
        (capture.model_dump_json() + "\n") * 2,
        encoding="utf-8",
    )

    with pytest.raises(
        ClassificationReplayError,
        match="Duplicate classification capture",
    ):
        read_classification_captures(path)


def test_malformed_capture_file_is_rejected(
    capture, tmp_path
):
    path = tmp_path / "captures.jsonl"

    path.write_text(
        capture.model_dump_json() + "\n"
        + "invalid JSON\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ClassificationReplayError,
        match="Invalid capture at line 2",
    ):
        read_classification_captures(path)


def test_empty_capture_file_round_trip(tmp_path):
    path = tmp_path / "captures.jsonl"

    write_classification_captures([], path)

    assert read_classification_captures(path) == []
