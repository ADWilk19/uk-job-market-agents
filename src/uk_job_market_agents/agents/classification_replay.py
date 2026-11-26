"""Deterministic classification capture and replay contracts."""

import hashlib
import json
from datetime import datetime
from collections.abc import Iterable
from pathlib import Path

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
)

from uk_job_market_agents.agents.classifier import (
    CLASSIFICATION_MODEL,
    ClassificationResult,
    build_classification_prompt,
)
from uk_job_market_agents.models.job_posting import JobPosting


def sha256_text(value: str) -> str:
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def classification_input_sha256(
    title: str,
    description: str,
) -> str:
    payload = json.dumps(
        {
            "title": title,
            "description": description,
        },
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    return sha256_text(payload)


class ClassificationCapture(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    source: str = Field(min_length=1)
    source_id: str = Field(min_length=1)

    input_sha256: str = Field(
        pattern=r"^[0-9a-f]{64}$"
    )

    prompt_sha256: str = Field(
        pattern=r"^[0-9a-f]{64}$"
    )

    model: str = Field(min_length=1)
    captured_at: AwareDatetime
    classification: ClassificationResult


def build_classification_capture(
    posting: JobPosting,
    classification: ClassificationResult,
    *,
    captured_at: datetime,
) -> ClassificationCapture:
    return ClassificationCapture(
        source=posting.source,
        source_id=posting.source_id,
        input_sha256=classification_input_sha256(
            posting.raw_title,
            posting.raw_description,
        ),
        prompt_sha256=sha256_text(
            build_classification_prompt(
                posting.raw_title,
                posting.raw_description,
            )
        ),
        model=CLASSIFICATION_MODEL,
        captured_at=captured_at,
        classification=classification,
    )


class ClassificationReplayError(ValueError):
    """A captured classification cannot safely be replayed."""


class ClassificationReplay:
    """Index and validate captured classification responses."""

    def __init__(
        self,
        captures: Iterable[ClassificationCapture],
    ) -> None:
        self._captures: dict[
            tuple[str, str], ClassificationCapture
        ] = {}

        for capture in captures:
            key = (capture.source, capture.source_id)

            if key in self._captures:
                raise ClassificationReplayError(
                    f"Duplicate classification capture: {key}"
                )

            self._captures[key] = capture.model_copy(
                deep=True
            )

    def classify(
        self,
        posting: JobPosting,
    ) -> ClassificationResult:
        key = (posting.source, posting.source_id)

        capture = self._captures.get(key)

        if capture is None:
            raise ClassificationReplayError(
                f"Missing classification capture: {key}"
            )

        expected_input = classification_input_sha256(
            posting.raw_title,
            posting.raw_description,
        )

        if capture.input_sha256 != expected_input:
            raise ClassificationReplayError(
                f"Classification input mismatch: {key}"
            )

        expected_prompt = sha256_text(
            build_classification_prompt(
                posting.raw_title,
                posting.raw_description,
            )
        )

        if capture.prompt_sha256 != expected_prompt:
            raise ClassificationReplayError(
                f"Classification prompt mismatch: {key}"
            )

        if capture.model != CLASSIFICATION_MODEL:
            raise ClassificationReplayError(
                f"Classification model mismatch: {key}"
            )

        return capture.classification.model_copy(
            deep=True
        )


def write_classification_captures(
    captures: Iterable[ClassificationCapture],
    path: Path,
) -> None:
    """Serialize validated captures to a JSON Lines file."""

    records = [
        ClassificationCapture.model_validate(
            capture.model_dump()
        )
        for capture in captures
    ]

    # Reject duplicate identities before writing.
    ClassificationReplay(records)

    payload = "".join(
        capture.model_dump_json() + "\n"
        for capture in records
    )

    with path.open(
        "x",
        encoding="utf-8",
        newline="\n",
    ) as file:
        file.write(payload)


def read_classification_captures(
    path: Path,
) -> list[ClassificationCapture]:
    """Load and validate persisted classification captures."""

    captures = []

    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            try:
                capture = (
                    ClassificationCapture.model_validate_json(
                        line
                    )
                )
            except ValueError as exc:
                raise ClassificationReplayError(
                    f"Invalid capture at line {line_number}"
                ) from exc

            captures.append(capture)

    # Reject duplicate identities before returning.
    ClassificationReplay(captures)

    return captures
