import json

from uk_job_market_agents.evaluation.comparison import (
    ClassificationComparison,
    ComparisonSummary,
)
from uk_job_market_agents.evaluation.history import (
    append_history_record,
    build_history_record,
    history_records_to_runs,
    load_history,
)
from uk_job_market_agents.models.job_posting import (
    RoleFamily,
    WorkPattern,
)


def test_build_history_record_serialises_enums():
    comparisons = [
        ClassificationComparison(
            title="Example",
            expected_role_family=RoleFamily.DATA_ENGINEERING,
            rules_role_family=RoleFamily.DATA_ENGINEERING,
            llm_role_family=RoleFamily.DATA_ENGINEERING,
            expected_work_pattern=WorkPattern.REMOTE,
            rules_work_pattern=WorkPattern.REMOTE,
            llm_work_pattern=WorkPattern.REMOTE,
        )
    ]

    summary = ComparisonSummary(
        total=1,
        rules_role_matches=1,
        llm_role_matches=1,
        rules_work_matches=1,
        llm_work_matches=1,
        rules_full_matches=1,
        llm_full_matches=1,
        classifier_disagreements=0,
    )

    record = build_history_record(comparisons, summary)

    assert record["summary"]["total"] == 1
    assert record["comparisons"][0]["llm_role_family"] == "data_engineering"
    assert record["comparisons"][0]["llm_work_pattern"] == "remote"


def test_append_history_record_creates_and_appends(tmp_path):
    path = tmp_path / "history.json"

    first = {"timestamp": "run-1"}
    second = {"timestamp": "run-2"}

    append_history_record(path, first)
    append_history_record(path, second)

    stored = json.loads(path.read_text())

    assert stored == [first, second]


def test_load_history_returns_empty_list_for_missing_file(tmp_path):
    path = tmp_path / "missing.json"

    assert load_history(path) == []


def test_history_records_to_runs_rebuilds_summaries():
    records = [
        {
            "timestamp": "run-1",
            "summary": {
                "total": 5,
                "rules_role_matches": 5,
                "llm_role_matches": 4,
                "rules_work_matches": 4,
                "llm_work_matches": 5,
                "rules_full_matches": 4,
                "llm_full_matches": 4,
                "classifier_disagreements": 2,
            },
            "comparisons": [],
        }
    ]

    runs = history_records_to_runs(records)

    assert len(runs) == 1
    assert runs[0].summary.llm_role_accuracy == 0.8
    assert runs[0].summary.llm_work_accuracy == 1.0
    assert runs[0].summary.disagreement_rate == 0.4
