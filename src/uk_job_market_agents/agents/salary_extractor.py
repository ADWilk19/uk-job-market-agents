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
