import pytest

from uk_job_market_agents.classification.rules import (
    classify_role_family,
    classify_work_pattern,
)
from uk_job_market_agents.models.job_posting import (
    RoleFamily,
    WorkPattern,
)


@pytest.mark.parametrize(
    ("title", "description", "expected"),
    [
        (
            "Data Engineer",
            "Build ETL pipelines using Python, SQL and Airflow.",
            RoleFamily.DATA_ENGINEERING,
        ),
        (
            "Analytics Engineer",
            "Build dbt models and maintain our analytics warehouse.",
            RoleFamily.ANALYTICS_ENGINEERING,
        ),
        (
            "Data Scientist",
            "Develop machine-learning models using Python.",
            RoleFamily.DATA_SCIENCE,
        ),
    ],
)
def test_classify_role_family(title, description, expected):
    assert classify_role_family(title, description) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "This is a fully remote UK position.",
            WorkPattern.REMOTE,
        ),
        (
            "Hybrid working with two days per week in our London office.",
            WorkPattern.HYBRID,
        ),
        (
            "This role is office based five days per week.",
            WorkPattern.ONSITE,
        ),
    ],
)
def test_classify_work_pattern(text, expected):
    assert classify_work_pattern(text) == expected


@pytest.mark.parametrize(
    (
        "title",
        "description",
        "expected_role_family",
        "expected_work_pattern",
    ),
    [
        # fictional-001
        (
            "Data Platform Specialist",
            '''We are looking for someone to build and maintain our analytics
            platform. You will develop ELT pipelines, maintain dbt models,
            optimise Snowflake, and work closely with analysts on semantic
            models.

            You should have strong SQL, dbt and Python skills.

            You will normally work from our London office two days per week.''',
            RoleFamily.DATA_ENGINEERING,
            WorkPattern.HYBRID,
        ),

        # fictional-002
        (
            "Data Engineer",
            '''Join our data platform team building production pipelines using
            Python, Airflow, AWS and PostgreSQL.

            This is a senior individual-contributor role.

            We normally meet in Bristol once every six weeks, but otherwise
            employees may work remotely anywhere in the UK.''',
            RoleFamily.DATA_ENGINEERING,
            WorkPattern.REMOTE,
        ),

        # fictional-003
        pytest.param(
            "Data Scientist",
            '''This is a remote-first role.

            You will build forecasting and optimisation models using Python,
            pandas, scikit-learn and SQL.

            All members of the team are expected to attend our Manchester
            office every Tuesday and Thursday.''',
            RoleFamily.DATA_SCIENCE,
            WorkPattern.HYBRID,
            marks=pytest.mark.xfail(
                reason=(
                    "Deterministic work-pattern rules match remote-first "
                    "before interpreting mandatory twice-weekly office attendance."
                )
            ),
        ),


        # fictional-004
        (
            "Early Career Analytics Engineer",
            '''Our two-year early-career programme is designed for people
            starting their career in analytics engineering.

            You will learn SQL, dbt and BigQuery while working alongside
            experienced analytics engineers.

            No previous analytics engineering experience is required.''',
            RoleFamily.ANALYTICS_ENGINEERING,
            WorkPattern.UNKNOWN,
        ),

        # fictional-005
        (
            "Lead Data Engineer — 6 month contract",
            '''Remote UK

            £650 per day, Inside IR35

            Lead the migration of an on-premise data warehouse to Azure.

            You will provide technical leadership while remaining hands-on
            with Python, SQL, Databricks and Azure Data Factory.

            Remote within the UK with quarterly meetings in Birmingham.''',
            RoleFamily.DATA_ENGINEERING,
            WorkPattern.REMOTE,
        ),
    ],
)
def test_golden_adverts(
    title,
    description,
    expected_role_family,
    expected_work_pattern,
):
    actual_role_family = classify_role_family(title, description)

    work_pattern_text = f"{title} {description}"
    actual_work_pattern = classify_work_pattern(work_pattern_text)

    assert actual_role_family == expected_role_family
    assert actual_work_pattern == expected_work_pattern
