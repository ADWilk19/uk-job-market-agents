from datetime import datetime, timezone

from uk_job_market_agents.ingestion.pipeline import (
    ingest_adzuna_jobs,
    prepare_adzuna_postings,
)


def test_prepare_adzuna_postings_adapts_and_deduplicates():
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

    collected_at = datetime(
        2026, 10, 26, 10, 0, tzinfo=timezone.utc
    )

    postings = prepare_adzuna_postings(
        advertisements,
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


def test_ingest_adzuna_jobs_fetches_adapts_and_deduplicates():
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

    calls = []

    def fake_fetch_pages(**kwargs):
        calls.append(kwargs)
        return advertisements

    collected_at = datetime(
        2026, 10, 26, 10, 0, tzinfo=timezone.utc
    )

    postings = ingest_adzuna_jobs(
        app_id="test-id",
        app_key="test-key",
        query="data engineer",
        max_pages=2,
        collected_at=collected_at,
        transport=None,
        fetch_pages=fake_fetch_pages,
    )

    assert len(calls) == 1
    assert calls[0]["query"] == "data engineer"
    assert calls[0]["max_pages"] == 2

    assert len(postings) == 2
    assert [posting.source_id for posting in postings] == [
        "101",
        "102",
    ]
