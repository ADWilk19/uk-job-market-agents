from pathlib import Path

from uk_job_market_agents.agents.classifier import classify_with_llm
from uk_job_market_agents.agents.workflow import (
    ClassificationWorkflowResult,
    adjudicate_workflow,
    resolve_after_adjudication,
    resolve_classification,
)
from uk_job_market_agents.classification.rules import (
    classify_role_family,
    classify_work_pattern,
)
from uk_job_market_agents.evaluation.comparison import (
    ClassificationComparison,
    summarise_comparisons,
    summarise_history,
)
from uk_job_market_agents.models.job_posting import (
    RoleFamily,
    WorkPattern,
)
from uk_job_market_agents.evaluation.history import (
    append_history_record,
    build_history_record,
    history_records_to_runs,
    load_history,
)


GOLDEN_ADVERTS = [
    (
        "Data Platform Specialist",
        """We are looking for someone to build and maintain our analytics
        platform. You will develop ELT pipelines, maintain dbt models,
        optimise Snowflake, and work closely with analysts on semantic
        models.

        You should have strong SQL, dbt and Python skills.

        You will normally work from our London office two days per week.""",
        RoleFamily.DATA_ENGINEERING,
        WorkPattern.HYBRID,
    ),
    (
        "Senior Data Engineer",
        """Join our data platform team building production pipelines using
        Python, Airflow, AWS and PostgreSQL.

        This is a senior individual-contributor role.

        We normally meet in Bristol once every six weeks, but otherwise
        employees may work remotely anywhere in the UK.""",
        RoleFamily.DATA_ENGINEERING,
        WorkPattern.REMOTE,
    ),
    (
        "Data Scientist",
        """This is a remote-first role.

        You will build forecasting and optimisation models using Python,
        pandas, scikit-learn and SQL.

        All members of the team are expected to attend our Manchester
        office every Tuesday and Thursday.""",
        RoleFamily.DATA_SCIENCE,
        WorkPattern.HYBRID,
    ),
    (
        "Early Career Analytics Engineer",
        """Our two-year early-career programme is designed for people
        starting their career in analytics engineering.

        You will learn SQL, dbt and BigQuery while working alongside
        experienced analytics engineers.

        No previous analytics engineering experience is required.""",
        RoleFamily.ANALYTICS_ENGINEERING,
        WorkPattern.UNKNOWN,
    ),
    (
        "Lead Data Engineer — 6 month contract",
        """Remote UK

        £650 per day, Inside IR35

        Lead the migration of an on-premise data warehouse to Azure.

        You will provide technical leadership while remaining hands-on
        with Python, SQL, Databricks and Azure Data Factory.

        Remote within the UK with quarterly meetings in Birmingham.""",
        RoleFamily.DATA_ENGINEERING,
        WorkPattern.REMOTE,
    ),
]
TABLE_WIDTH = 110
LABEL_WIDTH = 32
HISTORY_PATH = Path("data/evaluation_history.json")

def main() -> None:
    comparisons = []

    for title, description, expected_role, expected_work in GOLDEN_ADVERTS:
        rules_role_family = classify_role_family(
            title,
            description,
        )

        rules_work_pattern = classify_work_pattern(
            f"{title} {description}"
        )

        llm_result = classify_with_llm(
            title,
            description,
        )

        result = ClassificationComparison(
            title=title,
            expected_role_family=expected_role,
            rules_role_family=rules_role_family,
            llm_role_family=llm_result.role_family,
            expected_work_pattern=expected_work,
            rules_work_pattern=rules_work_pattern,
            llm_work_pattern=llm_result.work_pattern,
        )

        comparisons.append(result)

        workflow_result = ClassificationWorkflowResult.from_results(
            rules_role_family=rules_role_family,
            rules_work_pattern=rules_work_pattern,
            llm=llm_result,
        )

        adjudicated = adjudicate_workflow(
            title=title,
            description=description,
            result=workflow_result,
        )

        resolution = resolve_after_adjudication(adjudicated)

        print()
        print("=" * TABLE_WIDTH)
        print(title)
        print("-" * TABLE_WIDTH)

        print(
            f"Role family   "
            f"expected={result.expected_role_family.value:<24} "
            f"rules={result.rules_role_family.value:<24} "
            f"llm={result.llm_role_family.value}"
        )

        print(
            f"Work pattern  "
            f"expected={result.expected_work_pattern.value:<24} "
            f"rules={result.rules_work_pattern.value:<24} "
            f"llm={result.llm_work_pattern.value}"
        )

        if resolution.requires_review:
            print(
                f"Resolution     requires_review "
                f"proposed_role={resolution.proposed.role_family.value} "
                f"proposed_work={resolution.proposed.work_pattern.value}"
            )
        else:
            print(
                f"Resolution     auto_resolved "
                f"role={resolution.proposed.role_family.value} "
                f"work={resolution.proposed.work_pattern.value}"
            )

        if adjudicated.role_family_adjudication is not None:
                print(
                    "Role adjudication:",
                    adjudicated.role_family_adjudication.recommended_value.value,
                )

        if adjudicated.work_pattern_adjudication is not None:
            print(
                "Work adjudication:",
                adjudicated.work_pattern_adjudication.recommended_value.value,
            )

        print(
            "Proposed resolution:",
            resolution.proposed.role_family.value,
            "/",
            resolution.proposed.work_pattern.value,
        )

        print(
            "Requires review:",
            resolution.requires_review,
        )
    summary = summarise_comparisons(comparisons)

    record = build_history_record(
    comparisons,
    summary,
)

    append_history_record(
        HISTORY_PATH,
        record,
    )

    history_records = load_history(HISTORY_PATH)
    history_runs = history_records_to_runs(history_records)
    history_summary = summarise_history(history_runs)

    print()
    print("=" * TABLE_WIDTH)
    print("SUMMARY")
    print("-" * TABLE_WIDTH)
    print(f"Total adverts:                  {summary.total}")
    print(f"Rules role matches:             {summary.rules_role_matches}")
    print(f"LLM role matches:               {summary.llm_role_matches}")
    print(f"Rules work-pattern matches:     {summary.rules_work_matches}")
    print(f"LLM work-pattern matches:       {summary.llm_work_matches}")
    print(f"Classifier disagreements:       {summary.classifier_disagreements}")
    print()
    print("Evaluation metrics")
    print("-" * TABLE_WIDTH)

    print(f"{'Rules role accuracy:':<{LABEL_WIDTH}}{summary.rules_role_accuracy:.0%}")
    print(f"{'LLM role accuracy:':<{LABEL_WIDTH}}{summary.llm_role_accuracy:.0%}")
    print(f"{'Rules work accuracy:':<{LABEL_WIDTH}}{summary.rules_work_accuracy:.0%}")
    print(f"{'LLM work accuracy:':<{LABEL_WIDTH}}{summary.llm_work_accuracy:.0%}")
    print(f"{'Rules full accuracy:':<{LABEL_WIDTH}}{summary.rules_full_accuracy:.0%}")
    print(f"{'LLM full accuracy:':<{LABEL_WIDTH}}{summary.llm_full_accuracy:.0%}")
    print(f"{'Classifier disagreement rate:':<{LABEL_WIDTH}}{summary.disagreement_rate:.0%}")
    print(f"{'Review rate:':<{LABEL_WIDTH}}{summary.review_rate:.0%}")

    print()
    print("Evaluation history")
    print("-" * TABLE_WIDTH)
    print(f"Recorded runs:                 {history_summary.runs}")
    print(
        f"Average LLM role accuracy:     "
        f"{history_summary.average_llm_role_accuracy:.0%}"
    )
    print(
        f"Average LLM work accuracy:     "
        f"{history_summary.average_llm_work_accuracy:.0%}"
    )
    print(
        f"Average LLM full accuracy:     "
        f"{history_summary.average_llm_full_accuracy:.0%}"
    )
    print(
        f"Average disagreement rate:     "
        f"{history_summary.average_disagreement_rate:.0%}"
    )

if __name__ == "__main__":
    main()
