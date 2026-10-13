import pytest

from uk_job_market_agents.agents.salary_extractor import (
    SalaryExtractionResult,
    require_salary_evidence,
)


def test_accepts_salary_with_matching_evidence():
    advert = "Senior Data Engineer — £65,000–£80,000 per annum."

    result = SalaryExtractionResult(
        salary={
            "salary_min": 65000,
            "salary_max": 80000,
            "period": "year",
            "currency": "GBP",
        },
        evidence="£65,000–£80,000",
    )

    assert require_salary_evidence(advert, result) == result


def test_rejects_salary_without_evidence():
    result = SalaryExtractionResult(
        salary={
            "salary_min": 65000,
            "salary_max": 80000,
            "period": "year",
            "currency": "GBP",
        },
        evidence=None,
    )

    with pytest.raises(ValueError, match="supporting evidence"):
        require_salary_evidence(
            "Senior Data Engineer — £65,000–£80,000 per annum.",
            result,
        )


def test_rejects_evidence_not_found_in_advert():
    advert = "Senior Data Engineer — £65,000–£80,000 per annum."

    result = SalaryExtractionResult(
        salary={
            "salary_min": 90000,
            "salary_max": 110000,
            "period": "year",
            "currency": "GBP",
        },
        evidence="£90,000–£110,000",
    )

    with pytest.raises(ValueError, match="not found"):
        require_salary_evidence(advert, result)
