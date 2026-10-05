from uk_job_market_agents.agents.classifier import ClassificationResult
from uk_job_market_agents.evaluation.comparison import (
    ClassificationComparison,
    ClassificationDisagreement,
    ComparisonSummary,
    EvaluationRun,
    compare_classifiers,
    find_disagreements,
    summarise_comparisons,
    summarise_history,
)
from uk_job_market_agents.models.job_posting import (
    RoleFamily,
    WorkPattern,
)


def test_compare_classifiers(monkeypatch):
    def fake_llm_classifier(
        title: str,
        description: str,
    ) -> ClassificationResult:
        return ClassificationResult(
            role_family=RoleFamily.DATA_SCIENCE,
            work_pattern=WorkPattern.HYBRID,
            reasoning="Mandatory office attendance twice per week.",
        )

    monkeypatch.setattr(
        "uk_job_market_agents.evaluation.comparison.classify_with_llm",
        fake_llm_classifier,
    )

    result = compare_classifiers(
        title="Data Scientist",
        description=(
            "This is a remote-first role. "
            "All team members must attend the Manchester office "
            "every Tuesday and Thursday."
        ),
        expected_role_family=RoleFamily.DATA_SCIENCE,
        expected_work_pattern=WorkPattern.HYBRID,
    )

    assert result.expected_role_family == RoleFamily.DATA_SCIENCE
    assert result.rules_role_family == RoleFamily.DATA_SCIENCE
    assert result.llm_role_family == RoleFamily.DATA_SCIENCE

    assert result.expected_work_pattern == WorkPattern.HYBRID
    assert result.rules_work_pattern == WorkPattern.REMOTE
    assert result.llm_work_pattern == WorkPattern.HYBRID


def test_summarise_comparisons():
    comparisons = [
        ClassificationComparison(
            title="Example 1",
            expected_role_family=RoleFamily.DATA_ENGINEERING,
            rules_role_family=RoleFamily.DATA_ENGINEERING,
            llm_role_family=RoleFamily.DATA_ENGINEERING,
            expected_work_pattern=WorkPattern.REMOTE,
            rules_work_pattern=WorkPattern.REMOTE,
            llm_work_pattern=WorkPattern.REMOTE,
        ),
        ClassificationComparison(
            title="Example 2",
            expected_role_family=RoleFamily.DATA_SCIENCE,
            rules_role_family=RoleFamily.DATA_SCIENCE,
            llm_role_family=RoleFamily.DATA_SCIENCE,
            expected_work_pattern=WorkPattern.HYBRID,
            rules_work_pattern=WorkPattern.REMOTE,
            llm_work_pattern=WorkPattern.HYBRID,
        ),
    ]

    summary = summarise_comparisons(comparisons)

    assert summary.total == 2
    assert summary.rules_role_matches == 2
    assert summary.llm_role_matches == 2
    assert summary.rules_work_matches == 1
    assert summary.llm_work_matches == 2
    assert summary.classifier_disagreements == 1


def test_summary_calculates_evaluation_metrics():
    comparisons = [
        ClassificationComparison(
            title="Advert 1",
            expected_role_family=RoleFamily.DATA_ENGINEERING,
            rules_role_family=RoleFamily.DATA_ENGINEERING,
            llm_role_family=RoleFamily.DATA_ENGINEERING,
            expected_work_pattern=WorkPattern.REMOTE,
            rules_work_pattern=WorkPattern.REMOTE,
            llm_work_pattern=WorkPattern.REMOTE,
        ),
        ClassificationComparison(
            title="Advert 2",
            expected_role_family=RoleFamily.DATA_SCIENCE,
            rules_role_family=RoleFamily.DATA_SCIENCE,
            llm_role_family=RoleFamily.DATA_SCIENCE,
            expected_work_pattern=WorkPattern.HYBRID,
            rules_work_pattern=WorkPattern.REMOTE,
            llm_work_pattern=WorkPattern.HYBRID,
        ),
    ]

    summary = summarise_comparisons(comparisons)

    assert summary.total == 2

    assert summary.rules_role_accuracy == 1.0
    assert summary.llm_role_accuracy == 1.0

    assert summary.rules_work_accuracy == 0.5
    assert summary.llm_work_accuracy == 1.0

    assert summary.rules_full_accuracy == 0.5
    assert summary.llm_full_accuracy == 1.0

    assert summary.disagreement_rate == 0.5
    assert summary.review_rate == 0.5


def test_summary_rates_are_zero_for_empty_comparison_set():
    summary = summarise_comparisons([])

    assert summary.total == 0
    assert summary.rules_role_accuracy == 0.0
    assert summary.llm_role_accuracy == 0.0
    assert summary.rules_work_accuracy == 0.0
    assert summary.llm_work_accuracy == 0.0
    assert summary.rules_full_accuracy == 0.0
    assert summary.llm_full_accuracy == 0.0
    assert summary.disagreement_rate == 0.0
    assert summary.review_rate == 0.0


def test_summarise_history_calculates_average_metrics():
    run_one = EvaluationRun(
        summary=ComparisonSummary(
            total=5,
            rules_role_matches=5,
            llm_role_matches=4,
            rules_work_matches=4,
            llm_work_matches=5,
            rules_full_matches=4,
            llm_full_matches=4,
            classifier_disagreements=2,
        )
    )

    run_two = EvaluationRun(
        summary=ComparisonSummary(
            total=5,
            rules_role_matches=5,
            llm_role_matches=4,
            rules_work_matches=4,
            llm_work_matches=4,
            rules_full_matches=4,
            llm_full_matches=3,
            classifier_disagreements=3,
        )
    )

    history = summarise_history([run_one, run_two])

    assert history.runs == 2
    assert history.average_llm_role_accuracy == 0.8
    assert history.average_llm_work_accuracy == 0.9
    assert history.average_llm_full_accuracy == 0.7
    assert history.average_disagreement_rate == 0.5


def test_summarise_history_returns_zeroes_for_empty_history():
    history = summarise_history([])

    assert history.runs == 0
    assert history.average_llm_role_accuracy == 0.0
    assert history.average_llm_work_accuracy == 0.0
    assert history.average_llm_full_accuracy == 0.0
    assert history.average_disagreement_rate == 0.0


def test_find_disagreements_returns_only_disputed_classifications():
    comparisons = [
        ClassificationComparison(
            title="Stable advert",
            expected_role_family=RoleFamily.DATA_ENGINEERING,
            rules_role_family=RoleFamily.DATA_ENGINEERING,
            llm_role_family=RoleFamily.DATA_ENGINEERING,
            expected_work_pattern=WorkPattern.REMOTE,
            rules_work_pattern=WorkPattern.REMOTE,
            llm_work_pattern=WorkPattern.REMOTE,
        ),
        ClassificationComparison(
            title="Role disagreement",
            expected_role_family=RoleFamily.DATA_ENGINEERING,
            rules_role_family=RoleFamily.DATA_ENGINEERING,
            llm_role_family=RoleFamily.ANALYTICS_ENGINEERING,
            expected_work_pattern=WorkPattern.HYBRID,
            rules_work_pattern=WorkPattern.HYBRID,
            llm_work_pattern=WorkPattern.HYBRID,
        ),
        ClassificationComparison(
            title="Work disagreement",
            expected_role_family=RoleFamily.DATA_SCIENCE,
            rules_role_family=RoleFamily.DATA_SCIENCE,
            llm_role_family=RoleFamily.DATA_SCIENCE,
            expected_work_pattern=WorkPattern.HYBRID,
            rules_work_pattern=WorkPattern.REMOTE,
            llm_work_pattern=WorkPattern.HYBRID,
        ),
    ]

    assert find_disagreements(comparisons) == [
        ClassificationDisagreement(
            title="Role disagreement",
            role_family_disagreement=True,
            work_pattern_disagreement=False,
        ),
        ClassificationDisagreement(
            title="Work disagreement",
            role_family_disagreement=False,
            work_pattern_disagreement=True,
        ),
    ]
