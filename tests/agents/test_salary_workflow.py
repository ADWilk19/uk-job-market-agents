from uk_job_market_agents.agents.salary_extractor import (
    SalaryExtractionResult,
)
from uk_job_market_agents.agents.salary_review import (
    SalaryReviewStatus,
)
from uk_job_market_agents.agents.salary_workflow import (
    run_salary_workflow,
)


def test_salary_workflow_verifies_supported_extraction(monkeypatch):
    advert = "Senior Data Engineer — £65,000–£80,000 per annum"

    extraction = SalaryExtractionResult(
        salary={
            "salary_min": 65000,
            "salary_max": 80000,
            "period": "year",
            "currency": "GBP",
        },
        evidence="£65,000–£80,000 per annum",
    )

    def fake_extract(advert_text: str) -> SalaryExtractionResult:
        assert advert_text == advert
        return extraction

    monkeypatch.setattr(
        "uk_job_market_agents.agents.salary_workflow.extract_salary_with_llm",
        fake_extract,
    )

    result = run_salary_workflow(advert)

    assert result.status == SalaryReviewStatus.VERIFIED
    assert result.extraction == extraction
    assert result.reason is None


def test_salary_workflow_flags_unsupported_evidence(monkeypatch):
    advert = "Senior Data Engineer — £65k–£80k per annum"

    extraction = SalaryExtractionResult(
        salary={
            "salary_min": 65000,
            "salary_max": 80000,
            "period": "year",
            "currency": "GBP",
        },
        evidence="£65k–£80k per annum",
    )

    monkeypatch.setattr(
        "uk_job_market_agents.agents.salary_workflow.extract_salary_with_llm",
        lambda advert_text: extraction,
    )

    result = run_salary_workflow(advert)

    assert result.status == SalaryReviewStatus.REVIEW_REQUIRED
    assert result.extraction == extraction
    assert result.reason == "Unsupported salary evidence format"


def test_salary_workflow_handles_undisclosed_salary(monkeypatch):
    advert = "Senior Data Engineer — competitive salary"

    extraction = SalaryExtractionResult(
        salary=None,
        evidence=None,
    )

    monkeypatch.setattr(
        "uk_job_market_agents.agents.salary_workflow.extract_salary_with_llm",
        lambda advert_text: extraction,
    )

    result = run_salary_workflow(advert)

    assert result.status == SalaryReviewStatus.NOT_DISCLOSED
    assert result.extraction == extraction
    assert result.reason is None


