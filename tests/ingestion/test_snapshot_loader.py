import pytest
import json

from uk_job_market_agents.ingestion.snapshot_loader import (
    load_adzuna_snapshot,
)


def test_load_adzuna_snapshot(tmp_path):
    """Load an Adzuna snapshot and preserve its advertisement data."""
    snapshot_file = tmp_path / "snapshot.json"

    advertisement = {
        "id": "12345",
        "title": "Software Engineer",
        "description": "We are looking for a Software Engineer.",
        "location": {"display_name": "London"},
        "salary_min": 40000,
        "salary_max": 60000,
        "created": "2023-01-01T12:00:00Z",
    }

    snapshot_content = {"results": [advertisement]}

    snapshot_file.write_text(
        json.dumps(snapshot_content),
        encoding="utf-8",
    )

    loaded_ads = load_adzuna_snapshot(snapshot_file)

    assert loaded_ads == [advertisement]


def test_load_adzuna_snapshot_accepts_empty_results(tmp_path):
    """An empty result set is a valid Adzuna response."""
    snapshot_file = tmp_path / "empty_snapshot.json"

    snapshot_file.write_text(
        json.dumps({"results": []}),
        encoding="utf-8",
    )

    assert load_adzuna_snapshot(snapshot_file) == []


def test_load_adzuna_snapshot_rejects_missing_results(tmp_path):
    """Reject a snapshot without the required results field."""
    snapshot_file = tmp_path / "missing_results.json"

    snapshot_file.write_text(
        json.dumps({}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid Adzuna snapshot"):
        load_adzuna_snapshot(snapshot_file)


@pytest.mark.parametrize(
    "results",
    [
        None,
        "invalid",
        123,
        [123],
        [None],
        ["not an advertisement"],
        [{"id": "123"}, None],
    ],
)
def test_load_adzuna_snapshot_rejects_invalid_results(
    tmp_path,
    results,
):
    """Reject results that are not a list of advertisement objects."""
    snapshot_file = tmp_path / "invalid_results.json"

    snapshot_file.write_text(
        json.dumps({"results": results}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid Adzuna snapshot"):
        load_adzuna_snapshot(snapshot_file)


def test_load_adzuna_snapshot_rejects_malformed_json(tmp_path):
    """Reject a snapshot containing invalid JSON syntax."""
    snapshot_file = tmp_path / "malformed.json"

    snapshot_file.write_text(
        '{"results": [}',
        encoding="utf-8",
    )

    with pytest.raises(json.JSONDecodeError):
        load_adzuna_snapshot(snapshot_file)
