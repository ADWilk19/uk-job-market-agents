import pytest

from uk_job_market_agents.agents.salary_extractor import (
    SalaryExtractionResult,
)
from uk_job_market_agents.agents.salary_review import (
    SalaryAssessment,
    SalaryReviewStatus,
    assess_salary_extraction,
)
from uk_job_market_agents.models.salary import SalaryPeriod


def test_review_required_preserves_original_extraction():
    extraction = SalaryExtractionResult(
        salary={
            "salary_min": 65000,
            "salary_max": 80000,
            "period": "year",
            "currency": "GBP",
        },
        evidence="Competitive salary depending on experience",
    )

    assessment = SalaryAssessment(
        extraction=extraction,
        status=SalaryReviewStatus.REVIEW_REQUIRED,
        reason="Evidence format is not supported",
    )

    assert assessment.status == SalaryReviewStatus.REVIEW_REQUIRED
    assert assessment.extraction == extraction
    assert assessment.reason is not None


def test_assessment_identifies_undisclosed_salary():
    extraction = SalaryExtractionResult(
        salary=None,
        evidence=None,
    )

    assessment = assess_salary_extraction(
        advert_text="Senior Data Engineer. Competitive benefits.",
        extraction=extraction,
    )

    assert assessment.status == SalaryReviewStatus.NOT_DISCLOSED
    assert assessment.extraction == extraction
    assert assessment.reason is None


def test_verifies_matching_salary_range():
    advert = "Senior Data Engineer — £65,000–£80,000 per annum."

    extraction = SalaryExtractionResult(
        salary={
            "salary_min": 65000,
            "salary_max": 80000,
            "period": "year",
            "currency": "GBP",
        },
        evidence="£65,000–£80,000 per annum",
    )

    assessment = assess_salary_extraction(advert, extraction)

    assert assessment.status == SalaryReviewStatus.VERIFIED
    assert assessment.reason is None


def test_flags_salary_values_that_disagree_with_evidence():
    advert = "Senior Data Engineer — £65,000–£80,000 per annum."

    extraction = SalaryExtractionResult(
        salary={
            "salary_min": 90000,
            "salary_max": 110000,
            "period": "year",
            "currency": "GBP",
        },
        evidence="£65,000–£80,000 per annum",
    )

    assessment = assess_salary_extraction(advert, extraction)

    assert assessment.status == SalaryReviewStatus.REVIEW_REQUIRED
    assert assessment.extraction == extraction
    assert assessment.reason == "Extracted salary values disagree with evidence"


def test_flags_salary_period_not_supported_by_evidence():
    advert = "Senior Data Engineer — £65,000–£80,000 per day."

    extraction = SalaryExtractionResult(
        salary={
            "salary_min": 65000,
            "salary_max": 80000,
            "period": "year",
            "currency": "GBP",
        },
        evidence="£65,000–£80,000 per annum",
    )

    assessment = assess_salary_extraction(advert, extraction)

    assert assessment.status == SalaryReviewStatus.REVIEW_REQUIRED
    assert assessment.reason is not None


def test_flags_salary_period_mismatch():
    advert = "Senior Data Engineer — £650–£800 per day."

    extraction = SalaryExtractionResult(
        salary={
            "salary_min": 650,
            "salary_max": 800,
            "period": SalaryPeriod.YEAR,
            "currency": "GBP",
        },
        evidence="£650–£800 per day",
    )

    assessment = assess_salary_extraction(advert, extraction)

    assert assessment.status == SalaryReviewStatus.REVIEW_REQUIRED
    assert assessment.reason is not None


def test_verifies_matching_daily_salary():
    advert = "Contract Data Engineer — £650–£800 per day."

    extraction = SalaryExtractionResult(
        salary={
            "salary_min": 650,
            "salary_max": 800,
            "period": SalaryPeriod.DAY,
            "currency": "GBP",
        },
        evidence="£650–£800 per day",
    )

    assessment = assess_salary_extraction(advert, extraction)

    assert assessment.status == SalaryReviewStatus.VERIFIED
    assert assessment.reason is None


def test_flags_conflicting_salary_periods():
    advert = "Contract Data Engineer — £650–£800 per day annually."

    extraction = SalaryExtractionResult(
        salary={
            "salary_min": 650,
            "salary_max": 800,
            "period": SalaryPeriod.DAY,
            "currency": "GBP",
        },
        evidence="£650–£800 per day annually",
    )

    assessment = assess_salary_extraction(advert, extraction)

    assert assessment.status == SalaryReviewStatus.REVIEW_REQUIRED
    assert assessment.reason is not None


def test_verifies_salary_with_label_and_punctuation():
    advert = (
        "Senior Data Engineer. "
        "Salary: £65,000–£80,000 per annum. "
        "Hybrid working."
    )

    extraction = SalaryExtractionResult(
        salary={
            "salary_min": 65000,
            "salary_max": 80000,
            "period": SalaryPeriod.YEAR,
            "currency": "GBP",
        },
        evidence="Salary: £65,000–£80,000 per annum.",
    )

    assessment = assess_salary_extraction(advert, extraction)

    assert assessment.status == SalaryReviewStatus.VERIFIED
    assert assessment.reason is None


def test_verifies_abbreviated_annual_salary_range():
    advert = "Data Engineer — £45k–£55k per annum."

    extraction = SalaryExtractionResult(
        salary={
            "salary_min": 45000,
            "salary_max": 55000,
            "period": SalaryPeriod.YEAR,
            "currency": "GBP",
        },
        evidence="£45k–£55k per annum",
    )

    assessment = assess_salary_extraction(advert, extraction)

    assert assessment.status == SalaryReviewStatus.VERIFIED
    assert assessment.reason is None


@pytest.mark.parametrize(
    "evidence,salary_min,salary_max",
    [
        ("£42.5k–£55k per annum", 42500, 55000),
        ("£45K–£57.5K per year", 45000, 57500),
        ("£45,000–£55k annually", 45000, 55000),
        ("£42.5050k–£55,000 per annum", 42505, 55000),
    ],
)
def test_verifies_abbreviated_salary_variants(
    evidence, salary_min, salary_max
):
    extraction = SalaryExtractionResult(
        salary={
            "salary_min": salary_min,
            "salary_max": salary_max,
            "period": SalaryPeriod.YEAR,
            "currency": "GBP",
        },
        evidence=evidence,
    )

    assessment = assess_salary_extraction(evidence, extraction)

    assert assessment.status == SalaryReviewStatus.VERIFIED
    assert assessment.reason is None


@pytest.mark.parametrize(
    "evidence",
    [
        "£45k–£55k",
        "£45k–£55k per month",
        "£45k–55k per annum",
        "£45,00–£55k per annum",
        "£45.50–£55k per annum",
        "£45.0009k–£55k per annum",
        "£55k–£45k per annum",
        "£0k–£55k per annum",
    ],
)
def test_rejects_unsupported_salary_ranges(evidence):

    extraction = SalaryExtractionResult(
        salary={
            "salary_min": 45000,
            "salary_max": 55000,
            "period": SalaryPeriod.YEAR,
            "currency": "GBP",
        },
        evidence=evidence,
    )

    assessment = assess_salary_extraction(evidence, extraction)

    assert assessment.status == SalaryReviewStatus.REVIEW_REQUIRED
    assert assessment.reason == "Unsupported salary evidence format"


def test_rejects_evidence_that_cuts_off_a_period_word():
    extraction = SalaryExtractionResult(
        salary={
            "salary_min": 45,
            "salary_max": 55,
            "period": SalaryPeriod.HOUR,
        },
        evidence="£45–£55 per hour",
    )

    assessment = assess_salary_extraction("Pay is £45–£55 per hourly shift", extraction)

    assert assessment.status == SalaryReviewStatus.REVIEW_REQUIRED
    assert assessment.reason == "Evidence not found in advertisement"
