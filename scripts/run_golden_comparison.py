from uk_job_market_agents.evaluation.comparison import (
    compare_classifiers,
    summarise_comparisons,
)
from uk_job_market_agents.models.job_posting import (
    RoleFamily,
    WorkPattern,
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

def main() -> None:
    comparisons = []

    for title, description, expected_role, expected_work in GOLDEN_ADVERTS:
        result = compare_classifiers(
            title=title,
            description=description,
            expected_role_family=expected_role,
            expected_work_pattern=expected_work,
        )

        comparisons.append(result)

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

    summary = summarise_comparisons(comparisons)

    print()
    print("=" * TABLE_WIDTH)
    print("SUMMARY")
    print("-" * TABLE_WIDTH)
    print(f"Total adverts:              {summary.total}")
    print(f"Rules role matches:         {summary.rules_role_matches}")
    print(f"LLM role matches:           {summary.llm_role_matches}")
    print(f"Rules work-pattern matches: {summary.rules_work_matches}")
    print(f"LLM work-pattern matches:   {summary.llm_work_matches}")
    print(f"Classifier disagreements:   {summary.classifier_disagreements}")

if __name__ == "__main__":
    main()
