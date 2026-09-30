from dataclasses import dataclass

from uk_job_market_agents.agents.classifier import (
    ClassificationResult,
    classify_with_llm,
)
from uk_job_market_agents.classification.rules import (
    classify_role_family,
    classify_work_pattern,
)
from uk_job_market_agents.models.job_posting import (
    RoleFamily,
    WorkPattern,
)


@dataclass
class ClassificationComparison:
    title: str

    expected_role_family: RoleFamily
    rules_role_family: RoleFamily
    llm_role_family: RoleFamily

    expected_work_pattern: WorkPattern
    rules_work_pattern: WorkPattern
    llm_work_pattern: WorkPattern


@dataclass
class ComparisonSummary:
    total: int
    rules_role_matches: int
    llm_role_matches: int
    rules_work_matches: int
    llm_work_matches: int
    classifier_disagreements: int


def compare_classifiers(
    title: str,
    description: str,
    expected_role_family: RoleFamily,
    expected_work_pattern: WorkPattern,
) -> ClassificationComparison:
    rules_role_family = classify_role_family(title, description)

    rules_work_pattern = classify_work_pattern(
        f"{title} {description}"
    )

    llm_result: ClassificationResult = classify_with_llm(
        title,
        description,
    )

    return ClassificationComparison(
        title=title,
        expected_role_family=expected_role_family,
        rules_role_family=rules_role_family,
        llm_role_family=llm_result.role_family,
        expected_work_pattern=expected_work_pattern,
        rules_work_pattern=rules_work_pattern,
        llm_work_pattern=llm_result.work_pattern,
    )


def summarise_comparisons(
    comparisons: list[ClassificationComparison],
) -> ComparisonSummary:
    return ComparisonSummary(
        total=len(comparisons),
        rules_role_matches=sum(
            item.rules_role_family == item.expected_role_family
            for item in comparisons
        ),
        llm_role_matches=sum(
            item.llm_role_family == item.expected_role_family
            for item in comparisons
        ),
        rules_work_matches=sum(
            item.rules_work_pattern == item.expected_work_pattern
            for item in comparisons
        ),
        llm_work_matches=sum(
            item.llm_work_pattern == item.expected_work_pattern
            for item in comparisons
        ),
        classifier_disagreements=sum(
            (
                item.rules_role_family != item.llm_role_family
                or item.rules_work_pattern != item.llm_work_pattern
            )
            for item in comparisons
        ),
    )
