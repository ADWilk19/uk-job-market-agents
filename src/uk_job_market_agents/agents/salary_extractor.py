from openai import OpenAI

from pydantic import BaseModel, ConfigDict

from uk_job_market_agents.models.salary import SalaryQuote



class SalaryExtractionResult(BaseModel):
    """Represent a salary quotation extracted from an advertisement."""

    model_config = ConfigDict(extra="forbid")

    salary: SalaryQuote | None
    evidence: str | None


def require_salary_evidence(
    advert_text: str,
    result: SalaryExtractionResult,
) -> SalaryExtractionResult:
    """Require extracted salary evidence to appear in the advertisement."""

    if result.salary is None:
        if result.evidence is not None:
            raise ValueError(
                "Evidence cannot exist without an extracted salary"
            )
        return result

    if not result.evidence or not result.evidence.strip():
        raise ValueError(
            "Extracted salary requires supporting evidence"
        )

    if result.evidence not in advert_text:
        raise ValueError(
            "Salary evidence was not found in the advertisement"
        )

    return result


def extract_salary_with_llm(
    advert_text: str,
) -> SalaryExtractionResult:
    """Extract structured salary information from a job advertisement."""
    return _call_salary_model(advert_text)


def _call_salary_model(
    advert_text: str,
) -> SalaryExtractionResult:
    """Call OpenAI to extract structured salary information."""

    client = OpenAI()

    prompt = f"""
Extract salary information from the following UK job advertisement.

Return a salary quotation only when the advertisement explicitly
discloses a salary or pay rate.

Rules:
- Do not infer or estimate salaries.
- Extract the minimum and maximum amounts when provided.
- Use null for an unspecified bound.
- Identify the payment period: year, day, or hour.
- Use GBP as the currency.
- Copy the supporting salary evidence exactly from the advertisement.
- If no salary is disclosed, return null for both salary and evidence.
- Do not convert daily or hourly rates into annual salaries.

Advertisement:
{advert_text}
"""

    response = client.responses.parse(
        model="gpt-5.6-luna",
        input=prompt,
        text_format=SalaryExtractionResult,
    )

    result = response.output_parsed

    if result is None:
        raise RuntimeError(
            "Salary extractor did not return a parsed result"
        )

    return result
