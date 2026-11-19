import re
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict

from uk_job_market_agents.agents.salary_extractor import (
    SalaryExtractionResult,
)

from uk_job_market_agents.models.salary import SalaryPeriod

SALARY_RANGE_PATTERN = re.compile(
    r"(?:Salary:\s*)?"
    r"£(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?k|\d+)\s*[-–]\s*"
    r"£(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?k|\d+)"
    r"\s+(?:per annum|per year|annually|pa|per day|daily|per hour|hourly)(?!\w)"
    r"\.?",
    re.IGNORECASE,
)
PERIOD_EXPRESSIONS = {
    SalaryPeriod.YEAR: (
        "per annum",
        "per year",
        "annually",
        "pa",
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


PERIOD_PATTERN = "|".join(
    re.escape(expression)
    for expressions in PERIOD_EXPRESSIONS.values()
    for expression in expressions
)


@dataclass(frozen=True)
class SalaryEvidence:
    """Store recognised bounds, the stated period and precision."""

    salary_min: int
    salary_max: int
    period: SalaryPeriod | None
    approximate: bool = False


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

    evidence_pattern = re.escape(extraction.evidence)
    if extraction.evidence[-1].isalnum():
        evidence_pattern += r"(?!\w)"
    if extraction.evidence.rstrip()[-1:].isalnum():
        evidence_pattern += rf"(?!\s*(?i:{PERIOD_PATTERN})\b)"
    # A clipped quote can omit approximation or the first amount of a range.
    if not any(
        not re.search(
            r"(?:\bcirca\s+|£[\d,.]+k?\s*(?:[-–]|\bto)\s*)$",
            advert_text[:match.start()],
            re.IGNORECASE,
        )
        for match in re.finditer(evidence_pattern, advert_text)
    ):
        return SalaryAssessment(
            extraction=extraction,
            status=SalaryReviewStatus.REVIEW_REQUIRED,
            reason="Evidence not found in advertisement",
        )

    parsed_evidence = parse_salary_evidence(extraction.evidence)

    if (
        parsed_evidence is None
        or parsed_evidence.approximate
        or parsed_evidence.period is None
    ):
        return SalaryAssessment(
            extraction=extraction,
            status=SalaryReviewStatus.REVIEW_REQUIRED,
            reason="Unsupported salary evidence format",
        )

    if (
        extraction.salary.salary_min,
        extraction.salary.salary_max,
    ) != (
        parsed_evidence.salary_min,
        parsed_evidence.salary_max,
    ):
        return SalaryAssessment(
            extraction=extraction,
            status=SalaryReviewStatus.REVIEW_REQUIRED,
            reason="Extracted salary values disagree with evidence",
        )

    evidence_period = parsed_evidence.period

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


def parse_salary_amount(value: str) -> int | None:
    """Convert a matched GBP amount into whole pounds if exact."""

    normalized = value.replace(",", "").lower()

    try:
        if normalized.endswith("k"):
            pounds = Decimal(f"{normalized[:-1]}e3")
        else:
            pounds = Decimal(normalized)

        if not pounds.is_finite():
            return None

        if pounds != pounds.to_integral_value():
            return None

        return int(pounds)
    except (ValueError, ArithmeticError):
        return None


def parse_salary_range(evidence: str) -> tuple[int, int] | None:
    """Parse an explicit GBP salary range from evidence."""

    match = SALARY_RANGE_PATTERN.fullmatch(evidence.strip())

    if match is None:
        return None

    salary_min = parse_salary_amount(match.group(1))
    salary_max = parse_salary_amount(match.group(2))

    if salary_min is None or salary_max is None or not 0 < salary_min <= salary_max:
        return None

    return salary_min, salary_max


def parse_salary_evidence(evidence: str) -> SalaryEvidence | None:
    """Recognise GBP salary evidence without assuming its period."""

    amount = r"£((?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\d+(?:\.\d+)?k)"
    pattern = re.compile(
        rf"(?:Salary:\s*)?"
        rf"(?P<approx>circa\s+)?"
        rf"{amount}"
        rf"(?:(?:\s*[-–]\s*|\s+to\s+){amount})?"
        rf"(?:\s+(?P<period>{PERIOD_PATTERN})(?!\w))?"
        rf"\.?",
        re.IGNORECASE,
    )

    match = pattern.fullmatch(evidence.strip())

    if match is None:
        return None

    salary_min = parse_salary_amount(match.group(2))
    salary_max = parse_salary_amount(
        match.group(3) or match.group(2)
    )

    if (
        salary_min is None
        or salary_max is None
        or salary_min <= 0
        or salary_min > salary_max
    ):
        return None

    matched_period = (
        parse_salary_period(match.group("period"))
        if match.group("period")
        else None
    )

    return SalaryEvidence(
        salary_min=salary_min,
        salary_max=salary_max,
        period=matched_period,
        approximate=bool(match.group("approx")),
    )


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
