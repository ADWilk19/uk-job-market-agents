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
        evidence="£65,000–£80,000",
    )

    assessment = assess_salary_extraction(advert, extraction)

    assert assessment.status == SalaryReviewStatus.REVIEW_REQUIRED
    assert assessment.extraction == extraction
    assert assessment.reason is not None


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
