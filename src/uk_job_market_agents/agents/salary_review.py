import re
from enum import Enum

from pydantic import BaseModel, ConfigDict

from uk_job_market_agents.agents.salary_extractor import (
    SalaryExtractionResult,
)

from uk_job_market_agents.models.salary import SalaryPeriod

SALARY_RANGE_PATTERN = re.compile(
    r"£(\d{1,3}(?:,\d{3})+|\d+)\s*[-–]\s*"
    r"£(\d{1,3}(?:,\d{3})+|\d+)"
    r"\s+(?:per annum|per year|annually|per day|daily|per hour|hourly)",
    re.IGNORECASE,
)
PERIOD_EXPRESSIONS = {
    SalaryPeriod.YEAR: (
        "per annum",
        "per year",
        "annually",
    ),
    SalaryPeriod.DAY: (
        "per day",
        "daily",
    ),
    SalaryPeriod.HOUR: (
        "per hour",
        "hourly",
    ),
}


class SalaryReviewStatus(str, Enum):
    VERIFIED = "verified"
    REVIEW_REQUIRED = "review_required"
    NOT_DISCLOSED = "not_disclosed"


class SalaryAssessment(BaseModel):
    """Record the verification outcome of a salary extraction."""

    model_config = ConfigDict(extra="forbid")

    extraction: SalaryExtractionResult
    status: SalaryReviewStatus
    reason: str | None = None


def assess_salary_extraction(
    advert_text: str,
    extraction: SalaryExtractionResult,
) -> SalaryAssessment:
    """Assess extracted salary values against source evidence."""

    if extraction.salary is None and extraction.evidence is None:
        return SalaryAssessment(
            extraction=extraction,
            status=SalaryReviewStatus.NOT_DISCLOSED,
        )

    if extraction.salary is None or not extraction.evidence:
        return SalaryAssessment(
            extraction=extraction,
            status=SalaryReviewStatus.REVIEW_REQUIRED,
            reason="Incomplete salary extraction",
        )

    if extraction.evidence not in advert_text:
        return SalaryAssessment(
            extraction=extraction,
            status=SalaryReviewStatus.REVIEW_REQUIRED,
            reason="Evidence not found in advertisement",
        )

    parsed_range = parse_salary_range(extraction.evidence)

    if parsed_range is None:
        return SalaryAssessment(
            extraction=extraction,
            status=SalaryReviewStatus.REVIEW_REQUIRED,
            reason="Unsupported salary evidence format",
        )

    if (
        extraction.salary.salary_min,
        extraction.salary.salary_max,
    ) != parsed_range:
        return SalaryAssessment(
            extraction=extraction,
            status=SalaryReviewStatus.REVIEW_REQUIRED,
            reason="Extracted salary values disagree with evidence",
        )

    evidence_period = parse_salary_period(extraction.evidence)

    if evidence_period != extraction.salary.period:
        return SalaryAssessment(
            extraction=extraction,
            status=SalaryReviewStatus.REVIEW_REQUIRED,
            reason="Salary period is unsupported or disagrees with evidence",
        )

    return SalaryAssessment(
        extraction=extraction,
        status=SalaryReviewStatus.VERIFIED,
    )


def parse_salary_range(evidence: str) -> tuple[int, int] | None:
    """Parse an explicit GBP salary range from evidence."""

    match = SALARY_RANGE_PATTERN.fullmatch(evidence.strip())

    if match is None:
        return None

    salary_min = int(match.group(1).replace(",", ""))
    salary_max = int(match.group(2).replace(",", ""))

    return salary_min, salary_max


def parse_salary_period(evidence: str) -> SalaryPeriod | None:
    """Return the unambiguous salary period stated in the evidence."""

    text = evidence.lower()

    matches = {
        period
        for period, expressions in PERIOD_EXPRESSIONS.items()
        if any(
            re.search(rf"\b{re.escape(expression)}\b", text)
            for expression in expressions
        )
    }

    if len(matches) != 1:
        return None

    return matches.pop()
