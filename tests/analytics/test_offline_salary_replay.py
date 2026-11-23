
import csv
import json
from pathlib import Path

import pytest

from uk_job_market_agents.agents.salary_extractor import (
    SalaryExtractionResult,
)
from uk_job_market_agents.agents.salary_review import (
    SalaryReviewStatus,
    assess_salary_extraction,
    parse_salary_evidence,
    parse_salary_range,
)
from uk_job_market_agents.analytics.salary_policy import (
    is_salary_eligible_for_analytics,
)
from uk_job_market_agents.models.salary import SalaryPeriod, SalaryQuote


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests/fixtures/salary_evidence/observed_salary_evidence.csv"
SNAPSHOT = ROOT / "data/raw/adzuna_lesson36_20261116T092204Z.json"


def test_offline_salary_replay():
    if not SNAPSHOT.is_file():
        pytest.skip("Saved Lesson 36 Adzuna snapshot unavailable")

    with FIXTURE.open(encoding="utf-8", newline="") as file:
        cases = list(csv.DictReader(file))

    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    advertisements = {
        str(advert["id"]): advert
        for advert in snapshot["results"]
    }

    legacy_helper_recognised = 0
    updated_recognised = 0
    verified = 0
    annual_eligible = 0
    no_supported_period = 0

    for case in cases:
        evidence = case["evidence_text"]
        case_id = case["case_id"]

        legacy = parse_salary_range(evidence)
        parsed = parse_salary_evidence(evidence)

        legacy_helper_recognised += legacy is not None
        updated_recognised += parsed is not None

        assert parsed is not None, case_id
        assert case["source_snapshot"] == SNAPSHOT.name, case_id
        assert (parsed.salary_min, parsed.salary_max) == (
            int(case["expected_min_gbp"]), int(case["expected_max_gbp"])
        ), case_id
        assert (parsed.period.value if parsed.period else "unknown") == case["expected_period"], case_id
        assert parsed.approximate == (case["precision"] == "approximate"), case_id
        assert (legacy is not None) == (case_id == "observed_17"), case_id

        advert = advertisements[case["advertisement_id"]]
        assert evidence in advert["description"], case_id

        if parsed.period is None:
            no_supported_period += 1

        extraction = SalaryExtractionResult(
            salary=SalaryQuote(
                salary_min=parsed.salary_min,
                salary_max=parsed.salary_max,
                # Deliberately challenge verification with an invented annual
                # period when the quotation supplies none.
                period=parsed.period or SalaryPeriod.YEAR,
            ),
            evidence=evidence,
        )

        assessment = assess_salary_extraction(
            advert["description"],
            extraction,
        )

        expected_verified = (
            case["expected_period"] != "unknown" and case["precision"] == "exact"
        )
        assert assessment.status == (
            SalaryReviewStatus.VERIFIED if expected_verified
            else SalaryReviewStatus.REVIEW_REQUIRED
        ), case_id
        assert is_salary_eligible_for_analytics(assessment) == (
            expected_verified and case["expected_period"] == "year"
        ), case_id

        if assessment.status == SalaryReviewStatus.VERIFIED:
            verified += 1

        if is_salary_eligible_for_analytics(assessment):
            annual_eligible += 1
            assert parsed.period.value == "year"
            assert not parsed.approximate

    assert len(cases) == 8
    assert legacy_helper_recognised == 1
    assert updated_recognised == 8
    assert verified == 3
    assert annual_eligible == 1
    assert no_supported_period == 5


def test_offline_salary_replay_skips_without_snapshot(monkeypatch, tmp_path):
    monkeypatch.setitem(
        test_offline_salary_replay.__globals__, "SNAPSHOT", tmp_path / "missing.json"
    )
    with pytest.raises(pytest.skip.Exception, match="snapshot unavailable"):
        test_offline_salary_replay()


def test_approximate_annual_evidence_cannot_verify():
    # Isolate approximation from the unknown period in observed_16.
    evidence = "Circa £55,000 per year"
    extraction = SalaryExtractionResult(
        salary=SalaryQuote(salary_min=55000, salary_max=55000, period=SalaryPeriod.YEAR),
        evidence=evidence,
    )
    assessment = assess_salary_extraction(evidence, extraction)
    assert assessment.status == SalaryReviewStatus.REVIEW_REQUIRED
    assert not is_salary_eligible_for_analytics(assessment)
