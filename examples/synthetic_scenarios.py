"""Original synthetic scenarios for offline pipeline demonstrations."""

from datetime import datetime, timezone

from uk_job_market_agents.agents.classifier import (
    ClassificationResult,
)
from uk_job_market_agents.agents.salary_extractor import (
    SalaryExtractionResult,
)
from uk_job_market_agents.models.job_posting import (
    DescriptionCompleteness,
    JobPosting,
    RoleFamily,
    WorkPattern,
)
from uk_job_market_agents.models.salary import (
    SalaryPeriod,
    SalaryQuote,
)


def build_synthetic_postings() -> list[JobPosting]:
    """Return six independent synthetic job advertisements."""

    collected_at = datetime(
        2026, 11, 16, 9, 0, tzinfo=timezone.utc
    )

    def make_posting(
        source_id: str,
        description: str,
        completeness: DescriptionCompleteness = (
            DescriptionCompleteness.COMPLETE
        ),
        **kwargs,
    ) -> JobPosting:
        return JobPosting(
            source_id=source_id,
            source="synthetic",
            source_url=f"https://example.org/jobs/{source_id}",
            collected_at=collected_at,
            raw_title="Data Engineer",
            raw_description=description,
            description_completeness=completeness,
            **kwargs,
        )

    return [
        make_posting(
            "annual",
            "Fully remote role. Salary: £60,000 - £70,000 per year.",
        ),
        make_posting(
            "daily",
            "Fully remote role. Salary: £450 - £500 per day.",
        ),
        make_posting(
            "ambiguous",
            "Fully remote role. Salary: £55,000 - £65,000.",
        ),
        make_posting(
            "excerpt",
            "Fully remote role. Salary: £50,000 - £60,000 per year.",
            completeness=DescriptionCompleteness.EXCERPT,
            source_salary_min=50000,
            source_salary_max=60000,
            source_salary_predicted=True,
        ),
        make_posting(
            "review",
            "Fully remote role. Develop and maintain data pipelines.",
        ),
        make_posting(
            "failed",
            "Fully remote role. Maintain data infrastructure.",
        ),
    ]


def controlled_classification(
    source_id: str,
) -> ClassificationResult:
    """Return a predetermined synthetic classification."""

    if source_id == "failed":
        raise RuntimeError("Synthetic classification failure")

    return ClassificationResult(
        role_family=(
            RoleFamily.DATA_SCIENCE
            if source_id == "review"
            else RoleFamily.DATA_ENGINEERING
        ),
        work_pattern=WorkPattern.REMOTE,
        reasoning="Controlled classification response.",
    )


def controlled_salary_extraction(
    source_id: str,
) -> SalaryExtractionResult:
    """Return a predetermined synthetic salary extraction."""

    salary_candidates = {
        "annual": (
            60000,
            70000,
            SalaryPeriod.YEAR,
            "£60,000 - £70,000 per year",
        ),
        "daily": (
            450,
            500,
            SalaryPeriod.DAY,
            "£450 - £500 per day",
        ),
        "ambiguous": (
            55000,
            65000,
            SalaryPeriod.YEAR,
            "£55,000 - £65,000",
        ),
    }

    minimum, maximum, period, evidence = (
        salary_candidates[source_id]
    )

    return SalaryExtractionResult(
        salary=SalaryQuote(
            salary_min=minimum,
            salary_max=maximum,
            period=period,
        ),
        evidence=evidence,
    )
