from types import SimpleNamespace

import pytest

from uk_job_market_agents.agents.salary_extractor import (
    SalaryExtractionResult,
    require_salary_evidence,
    extract_salary_with_llm,
    _call_salary_model,
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


def test_extract_salary_with_llm_returns_structured_result(monkeypatch):
    expected = SalaryExtractionResult(
        salary={
            "salary_min": 65000,
            "salary_max": 80000,
            "period": "year",
            "currency": "GBP",
        },
        evidence="£65,000–£80,000 per annum",
    )

    def fake_model_call(advert_text: str) -> SalaryExtractionResult:
        return expected

    monkeypatch.setattr(
        "uk_job_market_agents.agents.salary_extractor._call_salary_model",
        fake_model_call,
    )

    result = extract_salary_with_llm(
        "Senior Data Engineer — £65,000–£80,000 per annum"
    )

    assert result == expected


def test_salary_model_returns_parsed_response(monkeypatch):
    expected = SalaryExtractionResult(
        salary={
            "salary_min": 65000,
            "salary_max": 80000,
            "period": "year",
            "currency": "GBP",
        },
        evidence="£65,000–£80,000 per annum",
    )

    def fake_parse(*, model, input, text_format):
        assert model
        assert "£65,000–£80,000 per annum" in input
        assert text_format is SalaryExtractionResult

        return SimpleNamespace(output_parsed=expected)

    fake_client = SimpleNamespace(
        responses=SimpleNamespace(parse=fake_parse)
    )

    monkeypatch.setattr(
        "uk_job_market_agents.agents.salary_extractor.OpenAI",
        lambda: fake_client,
    )

    result = _call_salary_model(
        "Senior Data Engineer — £65,000–£80,000 per annum"
    )

    assert result == expected


def test_salary_model_rejects_missing_parsed_response(monkeypatch):
    def fake_parse(*, model, input, text_format):
        return SimpleNamespace(output_parsed=None)

    fake_client = SimpleNamespace(
        responses=SimpleNamespace(parse=fake_parse)
    )

    monkeypatch.setattr(
        "uk_job_market_agents.agents.salary_extractor.OpenAI",
        lambda: fake_client,
    )

    with pytest.raises(
        RuntimeError,
        match="Salary extractor did not return a parsed result",
    ):
        _call_salary_model(
            "Senior Data Engineer — £65,000–£80,000 per annum"
        )
