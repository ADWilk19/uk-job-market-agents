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
    rules_full_matches: int
    llm_full_matches: int
    classifier_disagreements: int

    @staticmethod
    def _rate(matches: int, total: int) -> float:
        if total == 0:
            return 0.0

        return matches / total

    @property
    def rules_role_accuracy(self) -> float:
        return self._rate(self.rules_role_matches, self.total)

    @property
    def llm_role_accuracy(self) -> float:
        return self._rate(self.llm_role_matches, self.total)

    @property
    def rules_work_accuracy(self) -> float:
        return self._rate(self.rules_work_matches, self.total)

    @property
    def llm_work_accuracy(self) -> float:
        return self._rate(self.llm_work_matches, self.total)

    @property
    def rules_full_accuracy(self) -> float:
        return self._rate(self.rules_full_matches, self.total)

    @property
    def llm_full_accuracy(self) -> float:
        return self._rate(self.llm_full_matches, self.total)

    @property
    def disagreement_rate(self) -> float:
        return self._rate(self.classifier_disagreements, self.total)

    @property
    def review_rate(self) -> float:
        return self.disagreement_rate


@dataclass
class EvaluationRun:
    summary: ComparisonSummary


@dataclass
class EvaluationHistorySummary:
    runs: int
    average_llm_role_accuracy: float
    average_llm_work_accuracy: float
    average_llm_full_accuracy: float
    average_disagreement_rate: float


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
        rules_full_matches=sum(
            (
                item.rules_role_family == item.expected_role_family
                and item.rules_work_pattern == item.expected_work_pattern
            )
            for item in comparisons
        ),
        llm_full_matches=sum(
            (
                item.llm_role_family == item.expected_role_family
                and item.llm_work_pattern == item.expected_work_pattern
            )
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


def summarise_history(
    runs: list[EvaluationRun],
) -> EvaluationHistorySummary:
    if not runs:
        return EvaluationHistorySummary(
            runs=0,
            average_llm_role_accuracy=0.0,
            average_llm_work_accuracy=0.0,
            average_llm_full_accuracy=0.0,
            average_disagreement_rate=0.0,
        )

    total_runs = len(runs)

    return EvaluationHistorySummary(
        runs=total_runs,
        average_llm_role_accuracy=sum(
            run.summary.llm_role_accuracy
            for run in runs
        ) / total_runs,
        average_llm_work_accuracy=sum(
            run.summary.llm_work_accuracy
            for run in runs
        ) / total_runs,
        average_llm_full_accuracy=sum(
            run.summary.llm_full_accuracy
            for run in runs
        ) / total_runs,
        average_disagreement_rate=sum(
            run.summary.disagreement_rate
            for run in runs
        ) / total_runs,
    )


@dataclass(frozen=True)
class ClassificationDisagreement:
    title: str
    role_family_disagreement: bool
    work_pattern_disagreement: bool


def find_disagreements(
    comparisons: list[ClassificationComparison],
) -> list[ClassificationDisagreement]:
    disagreements = []

    for comparison in comparisons:
        role_disagreement = (
            comparison.rules_role_family
            != comparison.llm_role_family
        )
        work_disagreement = (
            comparison.rules_work_pattern
            != comparison.llm_work_pattern
        )

        if role_disagreement or work_disagreement:
            disagreements.append(
                ClassificationDisagreement(
                    title=comparison.title,
                    role_family_disagreement=role_disagreement,
                    work_pattern_disagreement=work_disagreement,
                )
            )

    return disagreements
