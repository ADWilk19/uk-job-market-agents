import json
from datetime import datetime, timezone

from uk_job_market_agents.ingestion.snapshot_pipeline import (
    prepare_adzuna_snapshot,
)


def test_prepare_adzuna_snapshot_adapts_and_deduplicates(tmp_path):
    """Load a saved response and produce unique JobPosting objects."""
    snapshot_file = tmp_path / "adzuna.json"

    advertisements = [
        {
            "id": "101",
            "title": "Data Engineer",
            "description": "Python and SQL engineering role",
        },
        {
            "id": "101",
            "title": "Data Engineer",
            "description": "Python and SQL engineering role",
        },
        {
            "id": "102",
            "title": "Data Analyst",
            "description": "Reporting and analytics role",
        },
    ]

    snapshot_file.write_text(
        json.dumps({"results": advertisements}),
        encoding="utf-8",
    )

    collected_at = datetime(
        2026, 10, 26, 10, 0, tzinfo=timezone.utc
    )

    postings = prepare_adzuna_snapshot(
        snapshot_file,
        collected_at=collected_at,
    )

    assert len(postings) == 2
    assert [posting.source_id for posting in postings] == [
        "101",
        "102",
    ]
    assert all(posting.source == "adzuna" for posting in postings)
    assert all(
        posting.collected_at == collected_at
        for posting in postings
    )
