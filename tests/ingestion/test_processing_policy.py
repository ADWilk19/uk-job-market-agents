
import pytest

from uk_job_market_agents.models.job_posting import (
    DescriptionCompleteness,
)
from uk_job_market_agents.ingestion.processing_policy import (
    should_attempt_salary_extraction,
)


@pytest.mark.parametrize(
    ("completeness", "expected"),
    [
        (DescriptionCompleteness.COMPLETE, True),
        (DescriptionCompleteness.EXCERPT, False),
        (DescriptionCompleteness.UNKNOWN, False),
    ],
)
def test_salary_extraction_requires_complete_description(
    completeness, expected
):
    assert should_attempt_salary_extraction(completeness) is expected
