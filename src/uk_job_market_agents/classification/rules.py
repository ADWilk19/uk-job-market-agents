from uk_job_market_agents.models.job_posting import RoleFamily, WorkPattern


def classify_role_family(title: str, description: str) -> RoleFamily:
    text = f"{title} {description}".lower()

    if "analytics engineer" in text:
        return RoleFamily.ANALYTICS_ENGINEERING

    if "data analyst" in text:
        return RoleFamily.DATA_ANALYTICS

    if any(
        term in text
        for term in (
            "data engineer",
            "data pipeline",
            "etl",
            "elt",
            "airflow",
            "dbt",
        )
    ):
        return RoleFamily.DATA_ENGINEERING

    if any(
        term in text
        for term in (
            "data scientist",
            "machine learning",
            "machine-learning",
            "predictive model",
        )
    ):
        return RoleFamily.DATA_SCIENCE

    return RoleFamily.OTHER


def classify_work_pattern(text: str) -> WorkPattern:
    normalised = text.lower()

    onsite_phrases = (
        "remote working is not available",
        "no remote working",
        "office based",
        "office-based",
        "on-site",
        "onsite",
    )

    if any(term in normalised for term in onsite_phrases):
        return WorkPattern.ONSITE

    remote_phrases = (
        "fully remote",
        "100% remote",
        "remote-first",
        "primarily remote",
        "work remotely",
        "remote uk",
        "remote within the uk",
    )

    if any(term in normalised for term in remote_phrases):
        return WorkPattern.REMOTE

    hybrid_phrases = (
        "hybrid",
        "days per week in the office",
        "days a week in the office",
        "office two days per week",
        "office two days a week",
    )

    if any(term in normalised for term in hybrid_phrases):
        return WorkPattern.HYBRID

    return WorkPattern.UNKNOWN
