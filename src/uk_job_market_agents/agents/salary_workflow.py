"""Coordinate LLM salary extraction and deterministic verification."""

from collections.abc import Callable

from uk_job_market_agents.agents.salary_extractor import (
    SalaryExtractionResult,
    extract_salary_with_llm,
)
from uk_job_market_agents.agents.salary_review import (
    SalaryAssessment,
    assess_salary_extraction,
)


def run_salary_workflow(
    advert_text: str,
    *,
    extractor: Callable[
        [str], SalaryExtractionResult
    ] | None = None,
) -> SalaryAssessment:
    """Extract salary information and assess it against the advert."""

    if extractor is None:
        extractor = extract_salary_with_llm

    extraction = extractor(advert_text)

    return assess_salary_extraction(
        advert_text=advert_text,
        extraction=extraction,
    )
