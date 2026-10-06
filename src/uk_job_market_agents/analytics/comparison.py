from dataclasses import dataclass
from enum import Enum

from uk_job_market_agents.analytics.summary import SalarySummary


class ComparisonStatus(str, Enum):
    OK = "ok"
    INSUFFICIENT_SAMPLE = "insufficient_sample"


@dataclass(frozen=True)
class SalaryComparison:
    status: ComparisonStatus
    difference: float | None
    reason: str | None


def compare_salary_summaries(
    left: SalarySummary,
    right: SalarySummary,
) -> SalaryComparison:
    if not left.has_sufficient_sample or not right.has_sufficient_sample:
        return SalaryComparison(
            status=ComparisonStatus.INSUFFICIENT_SAMPLE,
            difference=None,
            reason=(
                "Both groups require at least two salary-bearing records "
                "before a salary difference is reported."
            ),
        )

    assert left.average_midpoint is not None
    assert right.average_midpoint is not None

    return SalaryComparison(
        status=ComparisonStatus.OK,
        difference=left.average_midpoint - right.average_midpoint,
        reason=None,
    )
