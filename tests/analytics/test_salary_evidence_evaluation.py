import csv
from pathlib import Path

from uk_job_market_agents.agents.salary_review import parse_salary_range


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = (
    ROOT
    / "tests/fixtures/salary_evidence/observed_salary_evidence.csv"
)


def evaluate_salary_evidence(rows, parser):
    """Score parser recognition and numeric bounds for standalone quotations.

    Period, precision and eligibility are outside this score.
    """
    results = []

    for row in rows:
        expected = (
            int(row["expected_min_gbp"]),
            int(row["expected_max_gbp"]),
        )
        actual = parser(row["evidence_text"])

        results.append({
            "case_id": row["case_id"],
            "recognised": actual is not None,
            "numeric_match": actual == expected,
        })

    return results


def test_evaluator_distinguishes_recognition_and_correctness():
    rows = [
        {
            "case_id": "correct",
            "evidence_text": "correct",
            "expected_min_gbp": "45000",
            "expected_max_gbp": "55000",
        },
        {
            "case_id": "incorrect",
            "evidence_text": "incorrect",
            "expected_min_gbp": "45000",
            "expected_max_gbp": "55000",
        },
        {
            "case_id": "unrecognised",
            "evidence_text": "unrecognised",
            "expected_min_gbp": "45000",
            "expected_max_gbp": "55000",
        },
    ]

    outputs = {
        "correct": (45000, 55000),
        "incorrect": (40000, 60000),
        "unrecognised": None,
    }

    results = evaluate_salary_evidence(
        rows,
        parser=lambda evidence: outputs[evidence],
    )

    assert [result["recognised"] for result in results] == [
        True, True, False
    ]
    assert [result["numeric_match"] for result in results] == [
        True, False, False
    ]


def test_observed_evidence_evaluation_is_complete():
    with FIXTURE.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    results = evaluate_salary_evidence(rows, parse_salary_range)

    assert len(results) == len(rows)
    assert {result["case_id"] for result in results} == {
        row["case_id"] for row in rows
    }
    assert all(
        isinstance(result["recognised"], bool)
        and isinstance(result["numeric_match"], bool)
        for result in results
    )
