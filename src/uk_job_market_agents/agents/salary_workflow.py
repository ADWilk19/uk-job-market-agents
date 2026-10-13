"""Coordinate LLM salary extraction and deterministic verification."""

from uk_job_market_agents.agents.salary_extractor import (
    extract_salary_with_llm,
)
from uk_job_market_agents.agents.salary_review import (
    SalaryAssessment,
    assess_salary_extraction,
)


def run_salary_workflow(advert_text: str) -> SalaryAssessment:
    """Extract salary information and assess it against the advert."""

    extraction = extract_salary_with_llm(advert_text)

    return assess_salary_extraction(
        advert_text=advert_text,
        extraction=extraction,
    )
