"""Capture classifications for the Lesson 44 empirical population."""

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from uk_job_market_agents.agents.classifier import (
    classify_with_llm,
)
from uk_job_market_agents.agents.classification_replay import (
    ClassificationCapture,
    ClassificationReplay,
    build_classification_capture,
    read_classification_captures,
)
from uk_job_market_agents.ingestion.snapshot_pipeline import (
    prepare_adzuna_snapshot,
)
from uk_job_market_agents.models.job_posting import (
    DescriptionCompleteness,
    JobPosting,
)


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"

SNAPSHOTS = (
    "adzuna_lesson36_20261116T092204Z.json",
    "adzuna_analytics_engineer_20261116T093217Z.json",
    "adzuna_data_scientist_20261116T093219Z.json",
)

CAPTURE_PATH = RAW_DIR / "classification_lesson44.jsonl"
EXPECTED_POPULATION = 60


def load_population() -> list[JobPosting]:
    """Load and validate the saved empirical population."""

    postings = []

    for filename in SNAPSHOTS:
        path = RAW_DIR / filename
        metadata_path = path.with_suffix(".metadata.json")

        metadata = json.loads(
            metadata_path.read_text(encoding="utf-8")
        )

        if metadata["snapshot"] != filename:
            raise ValueError(f"Snapshot metadata mismatch: {filename}")

        if metadata["source"] != "adzuna":
            raise ValueError(f"Unexpected source: {filename}")

        collected_at = datetime.fromisoformat(
            metadata["collected_at"]
        )

        batch = prepare_adzuna_snapshot(
            path,
            collected_at=collected_at,
        )

        if len(batch) != metadata["requested_results"]:
            raise ValueError(f"Unexpected batch size: {filename}")

        postings.extend(batch)

    identities = {
        (posting.source, posting.source_id)
        for posting in postings
    }

    if len(postings) != EXPECTED_POPULATION:
        raise ValueError("Unexpected population size")

    if len(identities) != len(postings):
        raise ValueError("Duplicate posting identities")

    if any(
        posting.description_completeness
        != DescriptionCompleteness.EXCERPT
        for posting in postings
    ):
        raise ValueError("Population must contain only excerpts")

    return postings


def load_existing_captures(
    postings: list[JobPosting],
    path: Path,
) -> list[ClassificationCapture]:
    """Validate existing checkpoints against the population."""

    if not path.exists():
        return []

    captures = read_classification_captures(path)
    replay = ClassificationReplay(captures)

    population = {
        (posting.source, posting.source_id): posting
        for posting in postings
    }

    for capture in captures:
        key = (capture.source, capture.source_id)

        if key not in population:
            raise ValueError(f"Unexpected capture identity: {key}")

        replay.classify(population[key])

    return captures


def append_capture(
    capture: ClassificationCapture,
    path: Path,
) -> None:
    """Persist one successful classification checkpoint."""

    # A complete final JSON record may lack its newline after an interruption.
    # Existing records have already been validated before any API calls.
    separator = ""
    if path.exists() and path.stat().st_size:
        with path.open("rb") as existing:
            existing.seek(-1, os.SEEK_END)
            if existing.read(1) != b"\n":
                separator = "\n"

    with path.open(
        "a",
        encoding="utf-8",
        newline="\n",
    ) as file:
        file.write(separator + capture.model_dump_json() + "\n")
        file.flush()
        os.fsync(file.fileno())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)

    mode = parser.add_mutually_exclusive_group(required=True)

    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--limit", type=int)
    mode.add_argument("--all", action="store_true")

    args = parser.parse_args()

    if args.limit is not None and args.limit <= 0:
        parser.error("--limit must be positive")

    postings = load_population()

    captures = load_existing_captures(
        postings,
        CAPTURE_PATH,
    )

    captured_identities = {
        (capture.source, capture.source_id)
        for capture in captures
    }

    pending = [
        posting
        for posting in postings
        if (posting.source, posting.source_id)
        not in captured_identities
    ]

    print(f"Population: {len(postings)}")
    print(f"Existing compatible captures: {len(captures)}")
    print(f"Outstanding classifications: {len(pending)}")

    if args.dry_run:
        print("Dry run complete. No API calls made.")
        return

    selected = (
        pending
        if args.all
        else pending[:args.limit]
    )

    print(f"Classifications requested: {len(selected)}")

    for index, posting in enumerate(selected, start=1):
        classification = classify_with_llm(
            posting.raw_title,
            posting.raw_description,
        )

        capture = build_classification_capture(
            posting,
            classification,
            captured_at=datetime.now(timezone.utc),
        )

        append_capture(capture, CAPTURE_PATH)

        print(
            f"[{index}/{len(selected)}] "
            f"Captured {posting.source_id}",
            flush=True,
        )

    final_captures = load_existing_captures(
        postings,
        CAPTURE_PATH,
    )

    print(f"\nPersisted captures: {len(final_captures)}")
    print(
        "Outstanding classifications:",
        len(postings) - len(final_captures),
    )


if __name__ == "__main__":
    main()
