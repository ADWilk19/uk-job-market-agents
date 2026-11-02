from uk_job_market_agents.models.job_posting import DescriptionCompleteness


def should_attempt_salary_extraction(
    completeness: DescriptionCompleteness,
) -> bool:
    """
    Permit salary extraction only from complete job descriptions.

    Excerpts and unknown-completeness descriptions are excluded to
    prevent incomplete source evidence from affecting salary analysis.
    """
    return completeness == DescriptionCompleteness.COMPLETE
