"""Validate the standalone synthetic demonstration."""

import csv

import pytest

from examples.run_offline_demo import run_demo


def test_public_demo_is_reproducible(tmp_path, monkeypatch):
    # Injection must not fall back to either live interpretation function.
    def unexpected_call(*args, **kwargs):
        pytest.fail("Public demonstration attempted live inference")

    monkeypatch.setattr(
        "uk_job_market_agents.agents.workflow.classify_with_llm", unexpected_call
    )
    monkeypatch.setattr(
        "uk_job_market_agents.agents.salary_workflow.extract_salary_with_llm", unexpected_call
    )
    first = tmp_path / "first"
    second = tmp_path / "second"

    run_demo(first)
    run_demo(second)

    expected_files = {
        "jobs.csv",
        "batch_summary.csv",
        "analytical_samples.csv",
        "role_family_summary.csv",
    }

    assert {p.name for p in first.iterdir()} == expected_files
    assert {p.name for p in second.iterdir()} == expected_files

    for filename in expected_files:
        assert (
            (first / filename).read_bytes()
            == (second / filename).read_bytes()
        )

    with (first / "jobs.csv").open(
        encoding="utf-8", newline=""
    ) as file:
        jobs = list(csv.DictReader(file))

    assert len(jobs) == 6
    assert all(row["source"] == "synthetic" for row in jobs)

    with (first / "batch_summary.csv").open(
        encoding="utf-8", newline=""
    ) as file:
        summary = next(csv.DictReader(file))

    assert int(summary["total"]) == 6
    assert int(summary["processed"]) == 4
    assert int(summary["review_required"]) == 1
    assert int(summary["failed"]) == 1

    with (first / "analytical_samples.csv").open(
        encoding="utf-8", newline=""
    ) as file:
        samples = next(csv.DictReader(file))

    assert int(samples["total"]) == 6
    assert int(samples["role_eligible"]) == 4
    assert int(samples["salary_eligible"]) == 1


    by_id = {row["source_id"]: row for row in jobs}
    assert list(by_id) == ["annual", "daily", "ambiguous", "excerpt", "review", "failed"]
    assert [row["processing_status"] for row in jobs] == [
        "processed", "processed", "processed", "processed", "review_required", "failed",
    ]
    assert (by_id["annual"]["salary_min"], by_id["annual"]["salary_max"]) == ("60000", "70000")
    assert all(by_id[key]["salary_min"] == by_id[key]["salary_max"] == ""
               for key in by_id if key != "annual")
    assert by_id["excerpt"]["source_salary_min"] == "50000.0"
    assert by_id["excerpt"]["source_salary_max"] == "60000.0"
    assert by_id["excerpt"]["source_salary_predicted"] == "True"
    assert by_id["review"]["classification_review_reason"] == "role_family"
    assert by_id["ambiguous"]["classification_review_reason"] == ""
    assert float(samples["role_eligible_rate"]) == pytest.approx(4 / 6)
    assert float(samples["salary_eligible_rate"]) == pytest.approx(1 / 6)

    with (first / "role_family_summary.csv").open(encoding="utf-8", newline="") as file:
        groups = list(csv.DictReader(file))
    assert groups == [{
        "role_family": "data_engineering", "role_count": "4",
        "verified_salary_count": "1", "verified_salary_rate": "0.25",
    }]
    assert sum(int(g["role_count"]) for g in groups) == int(samples["role_eligible"])
    assert sum(int(g["verified_salary_count"]) for g in groups) == int(samples["salary_eligible"])

    # Reusing an output directory must also replace files deterministically.
    original = {name: (first / name).read_bytes() for name in expected_files}
    run_demo(first)
    assert {name: (first / name).read_bytes() for name in expected_files} == original
