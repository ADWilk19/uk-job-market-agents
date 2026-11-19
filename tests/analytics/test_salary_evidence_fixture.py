import csv
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]

FIXTURE = (
    ROOT
    / "tests/fixtures/salary_evidence/observed_salary_evidence.csv"
)

SNAPSHOT = (
    ROOT
    / "data/raw/adzuna_lesson36_20261116T092204Z.json"
)

EXPECTED_FIELDS = [
    "case_id",
    "source_snapshot",
    "advertisement_id",
    "evidence_text",
    "expected_min_gbp",
    "expected_max_gbp",
    "expected_period",
    "precision",
]


@pytest.fixture(scope="module")
def evidence_rows():
    with FIXTURE.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == EXPECTED_FIELDS
        rows = list(reader)
        for row in rows:
            assert None not in row, f"Extra columns in {row!r}"
            assert all(value and value.strip() for value in row.values()), row
            assert row["source_snapshot"] == SNAPSHOT.name
        return rows


@pytest.fixture(scope="module")
def source_records():
    try:
        payload = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    except FileNotFoundError:
        pytest.skip(f"Local provenance snapshot unavailable: {SNAPSHOT.name}")
    return {
        str(record["id"]): record
        for record in payload["results"]
    }


def test_fixture_identifiers_are_unique(evidence_rows):
    assert len(evidence_rows) == 8

    case_ids = [row["case_id"] for row in evidence_rows]
    advert_ids = [row["advertisement_id"] for row in evidence_rows]

    assert len(case_ids) == len(set(case_ids))
    assert len(advert_ids) == len(set(advert_ids))


def test_evidence_matches_original_advertisements(
    evidence_rows, source_records
):
    for row in evidence_rows:
        record = source_records[row["advertisement_id"]]

        assert row["evidence_text"] in record["description"], row["case_id"]


def test_expected_labels_are_consistent(evidence_rows):
    valid_periods = {"day", "year", "unknown"}
    valid_precisions = {"exact", "approximate"}

    for row in evidence_rows:
        minimum = int(row["expected_min_gbp"])
        maximum = int(row["expected_max_gbp"])

        assert 0 < minimum <= maximum
        assert row["expected_period"] in valid_periods
        assert row["precision"] in valid_precisions

        if row["precision"] == "approximate":
            assert minimum == maximum
