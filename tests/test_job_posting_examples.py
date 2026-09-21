from datetime import datetime

from uk_job_market_agents.models.job_posting import (
    JobPosting,
    RoleFamily,
    Seniority,
    WorkPattern,
)


def test_data_platform_specialist():
    job = JobPosting(
        source_id="fictional-001",
        source="lesson_fixture",
        collected_at=datetime.now(),
        raw_title="Data Platform Specialist",
        raw_description='''We are looking for someone to build and maintain our analytics
            platform. You will develop ELT pipelines, maintain dbt models,
            optimise Snowflake, and work closely with analysts on semantic
            models.

            You should have strong SQL, dbt and Python skills.

            You will normally work from our London office two days per week.''',
        location_raw="London",
        role_family=RoleFamily.DATA_ENGINEERING,
        seniority=Seniority.UNKNOWN,
        work_pattern=WorkPattern.HYBRID,
        salary_min=55000,
        salary_max=65000,
        skills=["SQL", "dbt", "Python"],
    )

    assert job.role_family == RoleFamily.DATA_ENGINEERING
    assert job.seniority == Seniority.UNKNOWN
    assert job.work_pattern == WorkPattern.HYBRID
    assert job.salary_min == 55000
    assert job.salary_max == 65000


def test_remote_senior_data_engineer():
    job = JobPosting(
        source_id="fictional-002",
        source="lesson_fixture",
        collected_at=datetime.now(),
        raw_title="Senior Data Engineer",
        raw_description='''Join our data platform team building production pipelines using
            Python, Airflow, AWS and PostgreSQL.

            This is a senior individual-contributor role.

            We normally meet in Bristol once every six weeks, but otherwise
            employees may work remotely anywhere in the UK.''',
        location_raw="Bristol / Remote",
        role_family=RoleFamily.DATA_ENGINEERING,
        seniority=Seniority.SENIOR,
        work_pattern=WorkPattern.REMOTE,
        salary_min=None,
        salary_max=None,
        skills=["Python", "Airflow", "AWS", "PostgreSQL"],
    )

    assert job.work_pattern == WorkPattern.REMOTE
    assert job.salary_min is None


def test_remote_first_data_scientist():
    job = JobPosting(
        source_id="fictional-003",
        source="lesson_fixture",
        collected_at=datetime.now(),
        raw_title="Data Scientist",
        raw_description='''This is a remote-first role.

        You will build forecasting and optimisation models using Python,
        pandas, scikit-learn and SQL.

        All members of the team are expected to attend our Manchester
        office every Tuesday and Thursday.''',
        location_raw="Manchester",
        role_family=RoleFamily.DATA_SCIENCE,
        seniority=Seniority.UNKNOWN,
        work_pattern=WorkPattern.HYBRID,
        salary_min=48000,
        salary_max=58000,
        skills=["Python", "pandas", "scikit-learn", "SQL"],
    )

    assert job.role_family == RoleFamily.DATA_SCIENCE
    assert job.work_pattern == WorkPattern.HYBRID
    assert job.salary_min == 48000
    assert job.salary_max == 58000


def test_early_career_analytics_engineer():
    job = JobPosting(
        source_id="fictional-004",
        source="lesson_fixture",
        collected_at=datetime.now(),
        raw_title="Early Career Analytics Engineer",
        raw_description='''Our two-year early-career programme is designed for people
            starting their career in analytics engineering.

            You will learn SQL, dbt and BigQuery while working alongside
            experienced analytics engineers.

            No previous analytics engineering experience is required.''',
        location_raw="Leeds",
        role_family=RoleFamily.ANALYTICS_ENGINEERING,
        seniority=Seniority.JUNIOR,
        work_pattern=WorkPattern.UNKNOWN,
        salary_min=32000,
        salary_max=38000,
        skills=["SQL", "dbt", "BigQuery"],
    )

    assert job.role_family == RoleFamily.ANALYTICS_ENGINEERING
    assert job.seniority == Seniority.JUNIOR
    assert job.work_pattern == WorkPattern.UNKNOWN
    assert job.salary_min == 32000
    assert job.salary_max == 38000


def test_lead_data_engineer_contract():
    job = JobPosting(
        source_id="fictional-005",
        source="lesson_fixture",
        collected_at=datetime.now(),
        raw_title="Lead Data Engineer — 6 month contract",
        raw_description='''Remote UK

            £650 per day, Inside IR35

            Lead the migration of an on-premise data warehouse to Azure.

            You will provide technical leadership while remaining hands-on
            with Python, SQL, Databricks and Azure Data Factory.

            Remote within the UK with quarterly meetings in Birmingham.''',
        location_raw="Remote UK",
        role_family=RoleFamily.DATA_ENGINEERING,
        seniority=Seniority.LEAD,
        work_pattern=WorkPattern.REMOTE,
        salary_min=None,
        salary_max=None,
        skills=["Python", "SQL", "Databricks", "Azure Data Factory"],
    )

    assert job.role_family == RoleFamily.DATA_ENGINEERING
    assert job.seniority == Seniority.LEAD
    assert job.work_pattern == WorkPattern.REMOTE
