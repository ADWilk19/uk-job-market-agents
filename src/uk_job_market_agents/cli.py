import argparse
import sys
import os
from pathlib import Path
from datetime import datetime

from collections.abc import Callable, Sequence

from uk_job_market_agents.agents.batch_orchestration import (
    BatchProcessingOutcome,
)
from uk_job_market_agents.ingestion.snapshot_execution import (
    run_snapshot_workflow,
)
from uk_job_market_agents.models.job_posting import JobPosting
from uk_job_market_agents.processing.processor_factory import create_processor


Processor = Callable[
    [list[JobPosting]],
    list[BatchProcessingOutcome],
]


def main(
    argv: Sequence[str] | None = None,
    *,
    processor: Processor | None = None,
) -> int:
    """Execute a saved snapshot using the selected processor."""
    parser = build_parser()
    args = parser.parse_args(argv)

    paths = {
        args.snapshot.resolve(),
        args.jobs_out.resolve(),
        args.summary_out.resolve(),
    }

    if len(paths) < 3:
        print(
            "Error: paths cannot be the same.",
            file=sys.stderr,
        )
        return 2

    if processor is None and args.mode == "agent":
        if not os.environ.get("OPENAI_API_KEY"):
            print(
                "Error: OPENAI_API_KEY is required for agent mode.",
                file=sys.stderr,
            )
            return 2

    selected_processor = (
        processor
        if processor is not None
        else create_processor(args.mode)
    )

    if processor is None and args.mode == "agent":
        print(
            "Warning: Agent processing may incur API costs.",
            file=sys.stderr,
        )

    try:
        _, summary = run_snapshot_workflow(
            snapshot_path=args.snapshot,
            collected_at=args.collected_at,
            processor=selected_processor,
            job_export_path=args.jobs_out,
            summary_export_path=args.summary_out,
        )
    except (OSError, ValueError) as exc:
        print(f"Execution error: {exc}", file=sys.stderr)
        return 2

    print(f"Total: {summary.total}")
    print(f"Processed: {summary.processed}")
    print(f"Review required: {summary.review_required}")
    print(f"Failed: {summary.failed}")

    return 1 if summary.failed > 0 else 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="python -m uk_job_market_agents",
        description="UK Job Market Agents CLI",
    )
    parser.add_argument("--snapshot", type=Path, required=True, help="Path to the snapshot JSON file")
    parser.add_argument(
        "--collected-at",
        type=parse_collected_at,
        required=True,
        help="Timezone-aware ISO 8601 collection timestamp"
    )
    parser.add_argument("--jobs-out", type=Path, required=True, help="Output path for jobs CSV")
    parser.add_argument("--summary-out", type=Path, required=True, help="Output path for summary CSV")
    parser.add_argument(
        "--mode",
        choices=("agent",),
        required=True,
        help="Processing implementation; agent mode may incur API costs",
    )

    return parser


def parse_collected_at(value: str) -> datetime:
    """Parse and validate a timezone-aware ISO 8601 timestamp."""
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "collected-at must be a valid ISO 8601 timestamp"
        ) from exc

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise argparse.ArgumentTypeError(
            "collected-at must include timezone information"
        )

    return parsed
