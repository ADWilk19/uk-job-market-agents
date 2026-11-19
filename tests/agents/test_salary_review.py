import pytest

from uk_job_market_agents.agents.salary_extractor import (
    SalaryExtractionResult,
)
from uk_job_market_agents.agents.salary_review import (
    SalaryAssessment,
    SalaryReviewStatus,
    assess_salary_extraction,
)
from uk_job_market_agents.analytics.salary_policy import (
    is_salary_eligible_for_analytics,
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


def test_verifies_observed_pa_annual_salary_range():
    evidence = "£76,000 - £95,000 pa"

    extraction = SalaryExtractionResult(
        salary={
            "salary_min": 76000,
            "salary_max": 95000,
            "period": SalaryPeriod.YEAR,
            "currency": "GBP",
        },
        evidence=evidence,
    )

    assessment = assess_salary_extraction(evidence, extraction)

    assert assessment.status == SalaryReviewStatus.VERIFIED
    assert assessment.reason is None
    assert is_salary_eligible_for_analytics(assessment)


@pytest.mark.parametrize(
    "evidence",
    [
        "£76,000 - £95,000 pa per day",
        "£76,000 - £95,000 pay",
        "£76,000 - £95,000",
    ],
)
def test_rejects_unsupported_pa_salary_evidence(evidence):
    extraction = SalaryExtractionResult(
        salary={
            "salary_min": 76000,
            "salary_max": 95000,
            "period": SalaryPeriod.YEAR,
            "currency": "GBP",
        },
        evidence=evidence,
    )

    assessment = assess_salary_extraction(evidence, extraction)

    assert assessment.status == SalaryReviewStatus.REVIEW_REQUIRED


@pytest.mark.parametrize(
    "evidence,salary_min,salary_max",
    [
        ("£450.00 - £500.00 per day", 450, 500),
        ("£500 per day", 500, 500),
    ],
)
def test_verifies_observed_daily_salary_evidence(
    evidence, salary_min, salary_max
):
    extraction = SalaryExtractionResult(
        salary={
            "salary_min": salary_min,
            "salary_max": salary_max,
            "period": SalaryPeriod.DAY,
            "currency": "GBP",
        },
        evidence=evidence,
    )

    assessment = assess_salary_extraction(evidence, extraction)

    assert assessment.status == SalaryReviewStatus.VERIFIED
    assert assessment.reason is None
    assert not is_salary_eligible_for_analytics(assessment)


@pytest.mark.parametrize(
    "evidence,salary_min,salary_max",
    [
        ("£95,000 - £105,000", 95000, 105000),
        ("Circa £55,000 pa", 55000, 55000),
    ],
)
def test_unverified_evidence_cannot_imply_annual_salary(
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

    assert assessment.status == SalaryReviewStatus.REVIEW_REQUIRED
    assert assessment.reason == "Unsupported salary evidence format"
    assert not is_salary_eligible_for_analytics(assessment)


@pytest.mark.parametrize(
    "advert_text",
    ["Circa £55k pa", "£45k – £55k pa", "£45k to £55k pa", "£55k pa PER DAY"],
)
def test_single_amount_cannot_omit_qualifying_text(advert_text):
    evidence = "£55k pa"
    extraction = SalaryExtractionResult(
        salary={
            "salary_min": 55000,
            "salary_max": 55000,
            "period": SalaryPeriod.YEAR,
            "currency": "GBP",
        },
        evidence=evidence,
    )

    assessment = assess_salary_extraction(advert_text, extraction)

    assert assessment.status == SalaryReviewStatus.REVIEW_REQUIRED
    assert not is_salary_eligible_for_analytics(assessment)


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
