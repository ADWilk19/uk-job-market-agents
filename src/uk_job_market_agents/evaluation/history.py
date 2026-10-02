import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from uk_job_market_agents.evaluation.comparison import (
    ClassificationComparison,
    ComparisonSummary,
)


def build_history_record(
    comparisons: list[ClassificationComparison],
    summary: ComparisonSummary,
) -> dict:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": asdict(summary),
        "comparisons": [
            {
                "title": item.title,
                "expected_role_family": item.expected_role_family.value,
                "rules_role_family": item.rules_role_family.value,
                "llm_role_family": item.llm_role_family.value,
                "expected_work_pattern": item.expected_work_pattern.value,
                "rules_work_pattern": item.rules_work_pattern.value,
                "llm_work_pattern": item.llm_work_pattern.value,
            }
            for item in comparisons
        ],
    }


def append_history_record(
    path: Path,
    record: dict,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        existing = json.loads(path.read_text())
    else:
        existing = []

    existing.append(record)

    path.write_text(
        json.dumps(existing, indent=2)
    )
