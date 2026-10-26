from dataclasses import dataclass

from uk_job_market_agents.ingestion.deduplication import (
    deduplicate_postings,
)


@dataclass(frozen=True)
class PostingStub:
    source: str
    source_id: str


def test_deduplicate_postings_preserves_first_seen_order():
    postings = [
        PostingStub("adzuna", "101"),
        PostingStub("adzuna", "102"),
        PostingStub("adzuna", "101"),
        PostingStub("adzuna", "103"),
    ]

    result = deduplicate_postings(postings)

    assert result == [
        postings[0],
        postings[1],
        postings[3],
    ]


def test_deduplicate_postings_distinguishes_sources():
    postings = [
        PostingStub("adzuna", "102"),
        PostingStub("another_provider", "102"),
    ]

    result = deduplicate_postings(postings)

    assert result == postings
